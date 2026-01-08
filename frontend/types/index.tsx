import { InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  placeholder?: string;
  value: string;
  type?: string;
  onValueChange: (value: string) => void;
  className?: string;
  onFocus?: () => void;
}

export interface ButtonProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  isLoading?: boolean;
}

export interface EditControlsProps {
  onSave: () => void;
  onCancel: () => void;
  onEdit: () => void;
  editMode: boolean;
  field: 'if' | 'then' | 'variantA' | 'variantB';
}

export interface Hypothesis {
  checked: boolean;
  editMode: {
    if: boolean;
    then: boolean;
    variantA: boolean;
    variantB: boolean;
  };
  current: {
    if: string;
    then: string;
    variantA: string;
    variantB: string;
  };
  temp: {
    if: string;
    then: string;
    variantA: string;
    variantB: string;
  };
}

export interface TextAreaProps {
  hypothesis: Hypothesis;
  handleChange: (
    field: 'if' | 'then' | 'variantA' | 'variantB',
    value: string
  ) => void;
  field: 'if' | 'then' | 'variantA' | 'variantB';
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
  isActive?: boolean;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export interface DropdownInputProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}

export interface HypothesisContainerProps {
  hypothesis: Hypothesis;
  title: string;
  primaryMetric: string;
  secondaryMetric: string;
  impactPercentage: number;
  impactLevel: 'High' | 'Medium' | 'Low';
  inspiration: string;
  onHypothesisChange: (updatedHypothesis: Hypothesis) => void;
}