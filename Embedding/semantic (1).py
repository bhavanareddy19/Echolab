"""
Semantic Search System for GitHub Issues (With 0.5 Similarity Threshold Clustering)
This script implements semantic search to find similar issues based on embedded vectors.
Modified to ensure issues only join clusters if similarity >= 0.5
"""

import pandas as pd
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import warnings
warnings.filterwarnings('ignore')

class SemanticSearchEngine:
    """
    A semantic search engine for GitHub issues using embedded vectors.
    """
    
    def __init__(self, csv_file):
        """
        Initialize the search engine with embedded vectors.
        
        Args:
            csv_file (str): Path to CSV file with embeddings
        """
        self.csv_file = csv_file
        self.df = None
        self.embeddings = None
        self.embeddings_normalized = None
        
    def load_data(self):
        """Load and prepare the embedded vectors for search."""
        print("="*70)
        print("SEMANTIC SEARCH ENGINE FOR GITHUB ISSUES")
        print("="*70)
        
        print(f"\n📂 Loading embedded vectors from: {self.csv_file}")
        self.df = pd.read_csv(self.csv_file)
        
        print(f"📊 Total issues in database: {len(self.df)}")
        print(f"📊 Columns found: {list(self.df.columns)}")
        
        # Parse embeddings
        embeddings_list = []
        valid_indices = []
        
        print("🔄 Parsing embedded vectors...")
        for idx, row in self.df.iterrows():
            try:
                embedding = json.loads(row['embedding'])
                embeddings_list.append(embedding)
                valid_indices.append(idx)
            except Exception as e:
                print(f"  ⚠ Skipping row {idx}: invalid embedding")
                continue
        
        # Convert to numpy array
        self.embeddings = np.array(embeddings_list)
        self.df = self.df.iloc[valid_indices].reset_index(drop=True)
        
        # Normalize embeddings for cosine similarity
        self.embeddings_normalized = normalize(self.embeddings, norm='l2')
        
        print(f"✓ Successfully loaded {len(self.embeddings)} embedded vectors")
        print(f"✓ Vector dimension: {self.embeddings.shape[1]}")
        
        # Show sample data structure
        print(f"\n📋 Sample data:")
        sample_body = self.df.iloc[0]['body'][:100] if len(self.df) > 0 else "No data"
        print(f"   Sample body: {sample_body}...")
        
        print("\n✅ Search engine ready!")
        
    def search_by_issue_id(self, issue_id, top_k=10, threshold=0.5):
        """
        Find issues similar to a given issue ID.
        
        Args:
            issue_id: ID of the query issue (can be string or int)
            top_k (int): Number of similar issues to return
            threshold (float): Minimum similarity score (0-1)
            
        Returns:
            DataFrame: Similar issues with similarity scores
        """
        # Convert issue_id to same type as in dataframe
        if issue_id not in self.df['id'].values:
            print(f"❌ Issue ID '{issue_id}' not found in database")
            available_ids = self.df['id'].head(10).tolist()
            print(f"💡 Available IDs (first 10): {available_ids}")
            return pd.DataFrame()
        
        # Get the issue's embedding
        issue_idx = self.df[self.df['id'] == issue_id].index[0]
        query_embedding = self.embeddings_normalized[issue_idx:issue_idx+1]
        
        # Get issue body for display
        query_body = self.df.loc[issue_idx, 'body'][:200]
        
        print(f"\n🔍 Searching for issues similar to:")
        print(f"   ID: {issue_id}")
        print(f"   Body: {query_body}...")
        
        return self._search_with_vector(query_embedding, top_k, threshold, exclude_idx=issue_idx)
    
    def search_by_vector(self, query_vector, top_k=10, threshold=0.5):
        """
        Find issues similar to a given vector.
        
        Args:
            query_vector (np.array): Query embedding vector
            top_k (int): Number of similar issues to return
            threshold (float): Minimum similarity score (0-1)
            
        Returns:
            DataFrame: Similar issues with similarity scores
        """
        # Normalize the query vector
        query_normalized = normalize(query_vector.reshape(1, -1), norm='l2')
        
        print(f"\n🔍 Searching for similar issues using provided vector...")
        
        return self._search_with_vector(query_normalized, top_k, threshold)
    
    def _search_with_vector(self, query_vector, top_k=10, threshold=0.5, exclude_idx=None):
        """
        Internal method to search with a normalized query vector.
        
        Args:
            query_vector (np.array): Normalized query vector (1, dim)
            top_k (int): Number of results
            threshold (float): Minimum similarity
            exclude_idx (int): Index to exclude (for self-search)
            
        Returns:
            DataFrame: Search results
        """
        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector, self.embeddings_normalized)[0]
        
        # Exclude the query issue itself if specified
        if exclude_idx is not None:
            similarities[exclude_idx] = -1
        
        # Find top-k most similar
        top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get extra in case of filtering
        
        # Prepare results
        results = []
        for idx in top_indices:
            if similarities[idx] < threshold:
                break
            if len(results) >= top_k:
                break
                
            results.append({
                'id': self.df.loc[idx, 'id'],
                'similarity_score': similarities[idx],
                'body': self.df.loc[idx, 'body']
            })
        
        if not results:
            print(f"⚠ No issues found with similarity >= {threshold}")
            return pd.DataFrame()
        
        results_df = pd.DataFrame(results)
        
        print(f"\n✓ Found {len(results_df)} similar issues")
        print(f"📊 Similarity range: {results_df['similarity_score'].min():.3f} - {results_df['similarity_score'].max():.3f}")
        
        return results_df
    
    def create_similarity_groups_with_threshold(self, n_groups=None, similarity_threshold=0.5):
        """
        Create groups of similar issues with a minimum similarity threshold.
        Issues that don't meet the threshold with any group get assigned to new groups.
        
        Args:
            n_groups (int): Maximum number of initial groups (optional)
            similarity_threshold (float): Minimum similarity to join a group (default: 0.5)
            
        Returns:
            DataFrame: Issues with group assignments
        """
        print(f"\n🔧 Creating groups with similarity threshold ≥ {similarity_threshold}...")
        
        n_issues = len(self.df)
        
        # Start with empty groups
        groups = []  # Each group will store representative indices
        group_assignments = [-1] * n_issues  # -1 means unassigned
        distances_to_rep = [0.0] * n_issues
        
        # Process each issue
        for i in range(n_issues):
            current_embedding = self.embeddings_normalized[i:i+1]
            best_group = -1
            best_similarity = -1
            
            # Check similarity to existing group representatives
            for group_idx, rep_indices in enumerate(groups):
                # Calculate similarity to group representative (first issue in group)
                rep_embedding = self.embeddings_normalized[rep_indices[0]:rep_indices[0]+1]
                similarity = cosine_similarity(current_embedding, rep_embedding)[0][0]
                
                if similarity >= similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_group = group_idx
            
            # Assign to best group or create new group
            if best_group >= 0:
                # Add to existing group
                groups[best_group].append(i)
                group_assignments[i] = best_group
                distances_to_rep[i] = best_similarity
            else:
                # Create new group with this issue as representative
                new_group_id = len(groups)
                groups.append([i])
                group_assignments[i] = new_group_id
                distances_to_rep[i] = 1.0  # Perfect similarity to itself
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{n_issues} issues, created {len(groups)} groups so far...")
        
        # Create result dataframe
        result_df = self.df.copy()
        result_df['group_id'] = group_assignments
        result_df['similarity_to_group_center'] = distances_to_rep
        
        # Sort by group and similarity
        result_df = result_df.sort_values(
            by=['group_id', 'similarity_to_group_center'],
            ascending=[True, False]
        )
        
        # Print group statistics
        print(f"\n📊 Final Group Statistics (threshold = {similarity_threshold}):")
        print("-"*60)
        
        group_sizes = result_df['group_id'].value_counts().sort_index()
        total_groups = len(group_sizes)
        
        print(f"Total groups created: {total_groups}")
        print(f"Average group size: {group_sizes.mean():.1f}")
        print(f"Largest group: {group_sizes.max()} issues")
        print(f"Smallest group: {group_sizes.min()} issues")
        
        # Show details for largest groups
        print(f"\nTop 10 largest groups:")
        for group_id in group_sizes.head(10).index:
            group_data = result_df[result_df['group_id'] == group_id]
            avg_sim = group_data['similarity_to_group_center'].mean()
            rep_body = group_data.iloc[0]['body'][:80]
            print(f"  Group {group_id}: {len(group_data)} issues, avg similarity: {avg_sim:.3f}")
            print(f"    Representative: {rep_body}...")
        
        print(f"\n✓ Clustering complete with threshold {similarity_threshold}")
        
        return result_df
    
    def create_similarity_groups(self, n_groups=50):
        """
        DEPRECATED: Create groups using old method (assigns to nearest regardless of similarity).
        Use create_similarity_groups_with_threshold() instead for quality clustering.
        """
        print(f"\n⚠ WARNING: This method doesn't use similarity thresholds!")
        print(f"   Consider using create_similarity_groups_with_threshold() instead")
        
        print(f"\n🔧 Creating {n_groups} similarity groups (old method)...")
        
        # Use a simple but effective approach: pick representatives and assign based on similarity
        n_issues = len(self.df)
        
        # Ensure we don't have more groups than issues
        n_groups = min(n_groups, n_issues)
        
        # Select representative issues (spread out in the embedding space)
        representatives = []
        remaining = list(range(n_issues))
        
        # Pick first representative randomly
        np.random.seed(42)  # For reproducible results
        first_rep = np.random.choice(remaining)
        representatives.append(first_rep)
        remaining.remove(first_rep)
        
        # Pick remaining representatives to be maximally different
        while len(representatives) < n_groups and remaining:
            # Calculate min distance to existing representatives
            min_sims = []
            for idx in remaining:
                sims_to_reps = [cosine_similarity(
                    self.embeddings_normalized[idx:idx+1],
                    self.embeddings_normalized[rep:rep+1]
                )[0][0] for rep in representatives]
                min_sims.append(min(sims_to_reps))
            
            # Pick the one with lowest similarity to existing representatives
            next_rep_idx = np.argmin(min_sims)
            next_rep = remaining[next_rep_idx]
            representatives.append(next_rep)
            remaining.remove(next_rep)
        
        # Assign all issues to nearest representative
        print("  Assigning issues to groups...")
        group_assignments = []
        distances_to_rep = []
        
        for i in range(n_issues):
            similarities = [cosine_similarity(
                self.embeddings_normalized[i:i+1],
                self.embeddings_normalized[rep:rep+1]
            )[0][0] for rep in representatives]
            
            best_group = np.argmax(similarities)
            best_similarity = similarities[best_group]
            
            group_assignments.append(best_group)
            distances_to_rep.append(best_similarity)
        
        # Add to dataframe
        result_df = self.df.copy()
        result_df['group_id'] = group_assignments
        result_df['similarity_to_group_center'] = distances_to_rep
        
        # Sort by group and similarity
        result_df = result_df.sort_values(
            by=['group_id', 'similarity_to_group_center'],
            ascending=[True, False]
        )
        
        # Print group statistics
        print("\n📊 Group Statistics:")
        print("-"*50)
        for group_id in range(len(representatives)):
            group_data = result_df[result_df['group_id'] == group_id]
            if len(group_data) > 0:
                avg_sim = group_data['similarity_to_group_center'].mean()
                print(f"Group {group_id}: {len(group_data)} issues, avg similarity: {avg_sim:.3f}")
                
                # Show representative and sample
                rep_idx = representatives[group_id]
                rep_body = self.df.loc[rep_idx, 'body'][:80]
                print(f"   Representative: {rep_body}...")
        
        print(f"\n✓ Created {len(representatives)} groups")
        
        return result_df
    
    def find_similar_groups(self, similarity_threshold=0.7, min_group_size=2):
        """
        Find groups of similar issues based on pairwise similarity.
        
        Args:
            similarity_threshold (float): Minimum similarity to be in same group
            min_group_size (int): Minimum size for a group
            
        Returns:
            list: Groups of similar issues
        """
        print(f"\n🔍 Finding groups of similar issues (threshold={similarity_threshold})...")
        
        # Calculate pairwise similarities
        print("  Calculating pairwise similarities...")
        similarity_matrix = cosine_similarity(self.embeddings_normalized)
        
        # Find groups using a greedy approach
        n_issues = len(self.df)
        visited = set()
        groups = []
        
        for i in range(n_issues):
            if i in visited:
                continue
                
            # Find all issues similar to this one
            similar_indices = np.where(similarity_matrix[i] >= similarity_threshold)[0]
            
            # Remove already visited issues
            similar_indices = [idx for idx in similar_indices if idx not in visited]
            
            if len(similar_indices) >= min_group_size:
                # Create a group
                group = {
                    'indices': similar_indices,
                    'size': len(similar_indices),
                    'avg_similarity': np.mean(similarity_matrix[i][similar_indices]),
                    'representative_idx': i,
                    'representative_id': self.df.loc[i, 'id'],
                    'representative_body': self.df.loc[i, 'body'][:150] + '...'
                }
                groups.append(group)
                visited.update(similar_indices)
        
        # Sort groups by size
        groups.sort(key=lambda x: x['size'], reverse=True)
        
        print(f"✓ Found {len(groups)} groups with {sum(g['size'] for g in groups)} total issues")
        
        return groups
    
    def batch_search(self, query_indices, top_k=5):
        """
        Perform batch search for multiple queries at once.
        
        Args:
            query_indices (list): List of indices or IDs to search for
            top_k (int): Number of similar issues for each query
            
        Returns:
            dict: Dictionary mapping query to similar issues
        """
        print(f"\n🔍 Performing batch search for {len(query_indices)} queries...")
        
        batch_results = {}
        
        for i, query in enumerate(query_indices):
            # Check if it's an ID or index
            if isinstance(query, str) or isinstance(query, int):
                results = self.search_by_issue_id(query, top_k=top_k, threshold=0.3)
                batch_results[query] = results
            else:
                query_vector = self.embeddings_normalized[query:query+1]
                results = self._search_with_vector(query_vector, top_k=top_k, exclude_idx=query)
                batch_results[self.df.loc[query, 'id']] = results
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(query_indices)} queries...")
        
        print(f"✓ Batch search complete")
        return batch_results
    
    def analyze_similarity_distribution(self):
        """Analyze the overall similarity distribution in the dataset."""
        print("\n📊 Analyzing similarity distribution...")
        
        # Calculate pairwise similarities for a sample
        n_sample = min(200, len(self.df))
        sample_embeddings = self.embeddings_normalized[:n_sample]
        similarity_matrix = cosine_similarity(sample_embeddings)
        
        # Get upper triangle (excluding diagonal)
        upper_triangle = np.triu(similarity_matrix, k=1)
        similarities = upper_triangle[upper_triangle > 0]
        
        print(f"\n📈 Similarity Statistics (sample of {n_sample} issues):")
        print(f"   Mean similarity: {similarities.mean():.4f}")
        print(f"   Std similarity: {similarities.std():.4f}")
        print(f"   Min similarity: {similarities.min():.4f}")
        print(f"   Max similarity: {similarities.max():.4f}")
        print(f"   Median similarity: {np.median(similarities):.4f}")
        
        # Show distribution
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        print(f"\n📊 Similarity Percentiles:")
        for p in percentiles:
            val = np.percentile(similarities, p)
            print(f"   {p}th percentile: {val:.4f}")
        
        return {
            'mean': similarities.mean(),
            'std': similarities.std(),
            'min': similarities.min(),
            'max': similarities.max(),
            'median': np.median(similarities),
            'percentiles': {p: np.percentile(similarities, p) for p in percentiles}
        }

def main():
    """
    Main function demonstrating semantic search capabilities with 0.5 threshold clustering.
    """
    # Configuration
    INPUT_FILE = 'embedding_minilm_l6_v2.csv'
    
    # Initialize search engine
    engine = SemanticSearchEngine(INPUT_FILE)
    
    try:
        # Load data
        engine.load_data()
        
        # Analyze similarity distribution first
        stats = engine.analyze_similarity_distribution()
        
        print("\n" + "="*70)
        print("SEMANTIC SEARCH OPERATIONS WITH 0.5 THRESHOLD")
        print("="*70)
        
        # 1. Create similarity groups with 0.5 threshold (NEW METHOD)
        print("\n1️⃣ Creating similarity-based groups with 0.5 threshold...")
        grouped_df = engine.create_similarity_groups_with_threshold(similarity_threshold=0.5)
        
        # Save grouped results
        output_columns = ['id', 'group_id', 'similarity_to_group_center', 'body']
        grouped_df[output_columns].to_csv(
            'issues_clustered_threshold_0.5.csv', index=False
        )
        print(f"✓ Saved clustered issues to 'issues_clustered_threshold_0.5.csv'")
        
        # 2. Compare with different thresholds
        print("\n2️⃣ Comparing clustering with different thresholds...")
        
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
        threshold_results = {}
        
        for threshold in thresholds:
            temp_df = engine.create_similarity_groups_with_threshold(similarity_threshold=threshold)
            n_groups = temp_df['group_id'].nunique()
            avg_group_size = len(temp_df) / n_groups
            avg_similarity = temp_df['similarity_to_group_center'].mean()
            
            threshold_results[threshold] = {
                'groups': n_groups,
                'avg_size': avg_group_size,
                'avg_similarity': avg_similarity
            }
            
            print(f"  Threshold {threshold}: {n_groups} groups, avg size: {avg_group_size:.1f}, avg similarity: {avg_similarity:.3f}")
        
        # 3. Find naturally occurring similar groups
        print("\n3️⃣ Finding naturally occurring similar groups...")
        similar_groups = engine.find_similar_groups(similarity_threshold=0.7, min_group_size=3)
        
        if similar_groups:
            print(f"\nTop 5 naturally similar groups (threshold=0.7):")
            for i, group in enumerate(similar_groups[:5], 1):
                print(f"\nGroup {i}:")
                print(f"  Size: {group['size']} issues")
                print(f"  Avg similarity: {group['avg_similarity']:.3f}")
                print(f"  Example: {group['representative_body']}")
        
        # 4. Example: Search for issues similar to the first issue
        print("\n4️⃣ Example search - Finding issues similar to first issue...")
        first_issue_id = engine.df.iloc[0]['id']
        similar_issues = engine.search_by_issue_id(first_issue_id, top_k=5, threshold=0.5)
        
        if not similar_issues.empty:
            print(f"\nTop 5 similar issues (threshold=0.5):")
            for idx, row in similar_issues.iterrows():
                print(f"\n  • ID: {row['id']}")
                print(f"    Similarity: {row['similarity_score']:.3f}")
                print(f"    Body: {row['body'][:100]}...")
            
            # Save example search results
            similar_issues.to_csv('example_search_results_threshold_0.5.csv', index=False)
            print(f"\n✓ Example search results saved to 'example_search_results_threshold_0.5.csv'")
        
        print("\n" + "="*70)
        print("✅ SEMANTIC SEARCH WITH 0.5 THRESHOLD COMPLETE!")
        print("="*70)
        print("\nKey Results:")
        print(f"  • Total issues processed: {len(engine.df)}")
        print(f"  • Groups created with 0.5 threshold: {grouped_df['group_id'].nunique()}")
        print(f"  • Average group similarity: {grouped_df['similarity_to_group_center'].mean():.3f}")
        print(f"  • Issues with similarity ≥ 0.5: {len(grouped_df[grouped_df['similarity_to_group_center'] >= 0.5])}")
        
        print("\nThreshold Comparison Results:")
        for threshold, results in threshold_results.items():
            print(f"  • {threshold}: {results['groups']} groups, avg similarity: {results['avg_similarity']:.3f}")
        
        print("\nOutput files created:")
        print("  • issues_clustered_threshold_0.5.csv - Issues clustered with 0.5 threshold")
        print("  • example_search_results_threshold_0.5.csv - Example search results")
        
        print("\n💡 Usage Examples:")
        print("# Create clusters with 0.5 threshold (recommended):")
        print("clustered = engine.create_similarity_groups_with_threshold(similarity_threshold=0.5)")
        print("\n# Create clusters with custom threshold:")
        print("clustered = engine.create_similarity_groups_with_threshold(similarity_threshold=0.6)")
        print("\n# Search for similar issues:")
        print(f"results = engine.search_by_issue_id({first_issue_id}, threshold=0.5)")
        
        # Return engine for interactive use
        return engine
        
    except FileNotFoundError:
        print(f"\n❌ Error: Could not find '{INPUT_FILE}'")
        print("Please ensure the file exists in the current directory.")
        return None
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def quick_cluster_with_threshold(csv_file, similarity_threshold=0.5, output_file=None):
    """
    Quick function to cluster issues with a specific threshold.
    
    Args:
        csv_file (str): Path to CSV with embeddings
        similarity_threshold (float): Minimum similarity to join group
        output_file (str): Output CSV filename (optional)
        
    Returns:
        DataFrame: Clustered issues
    """
    engine = SemanticSearchEngine(csv_file)
    engine.load_data()
    
    print(f"\n🚀 Quick clustering with threshold {similarity_threshold}...")
    clustered_df = engine.create_similarity_groups_with_threshold(similarity_threshold=similarity_threshold)
    
    if output_file:
        clustered_df[['id', 'group_id', 'similarity_to_group_center', 'body']].to_csv(
            output_file, index=False
        )
        print(f"✓ Results saved to '{output_file}'")
    
    return clustered_df

if __name__ == "__main__":
    # Run main pipeline
    engine = main()
    
    # The engine is now ready for interactive use with 0.5 threshold clustering
    # 
    # RECOMMENDED USAGE:
    # clustered = engine.create_similarity_groups_with_threshold(similarity_threshold=0.5)
    # 
    # OTHER COMMANDS:
    # engine.search_by_issue_id(issue_id, threshold=0.5)
    # engine.find_similar_groups(similarity_threshold=0.7)
    # engine.batch_search([id1, id2, id3], top_k=5)
    #
    # QUICK USAGE:
    # clustered = quick_cluster_with_threshold('embedding_minilm_l6_v2.csv', 0.5, 'my_clusters.csv')