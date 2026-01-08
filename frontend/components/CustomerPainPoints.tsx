import { IconTrendingUp, IconTrendingDown } from '@tabler/icons-react';
import { useRouter } from 'next/navigation';
export default function CustomerPainPoints() {

    const router = useRouter();


  const painPointsCards = [
    {
      title: 'Checkout Freezes',
      value: '211',
      change: '18%',
      changeType: 'negative' as const,
      tags: [
        { label: 'Feature', color: 'blue' },
        { label: 'New', color: 'gray' },
      ],
    },
    {
      title: 'Payment Declined',
      value: '189',
      change: '15%',
      changeType: 'negative' as const,
      tags: [
        { label: 'Bug', color: 'red' },
        { label: 'New', color: 'gray' },
      ],
    },
    {
      title: 'Slow Loading',
      value: '156',
      change: '12%',
      changeType: 'positive' as const,
      tags: [
        { label: 'Bug', color: 'red' },
        { label: 'In progress', color: 'yellow' },
      ],
    },
  ];

  const getTagStyles = (color: string) => {
    switch (color) {
      case 'blue':
        return 'rounded-[8px] border border-[#D4E6FF] bg-[#F6FAFF] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#4652DC]';
      case 'red':
        return 'rounded-[8px] border border-[#FFDCDC] bg-[#FFF2F2] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#F71111]';
      case 'yellow':
        return 'rounded-[8px] border border-[#FFE4B6] bg-[#FFFBE3] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#F09800]';
      case 'gray':
      default:
        return 'rounded-[8px] border border-[#8C8C8C] bg-[#F6F6F6] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-black';
    }
  };

  return (
    <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-row items-center justify-between">
              <p className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
                Customer Pain Points
              </p>
              <div className="bg-[#E8E8E8] rounded-[8px] px-3 py-2.5 text-black text-sm tracking-[0.5%] leading-[16px] font-medium cursor-pointer">
                View All
              </div>
            </div>

            <p className="text-[#7F7F7F] text-sm tracking-[0.5%] leading-[16px] font-normal">
              Top themes identified from 12,310 tickets in the last 90 days
            </p>
          </div>

          <div className="col-span-12">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-3">
              {painPointsCards.map((card, index) => (
                <div
                  key={index}
                  className="flex flex-col justify-between rounded-[8px] bg-primary py-4 px-3 gap-5 cursor-pointer hover:!bg-[#E8E8E8] hover:scale-102 transition-all duration-200"
                  onClick={() => {
                    router.push(`/dashboard/pain-points/${card.title}`);
                  }}>
                  <div className="flex flex-row items-center justify-between">
                    <div className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
                      {card.title}
                    </div>
                    <div className="flex gap-1">
                      {card.tags.map((tag, tagIndex) => (
                        <div key={tagIndex} className={getTagStyles(tag.color)}>
                          {tag.label}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-row items-center justify-between">
                    <div className="flex flex-col gap-1.5">
                      <div className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                        {card.value}
                      </div>
                      <div className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                        Tickets
                      </div>
                    </div>
                    <div className="flex flex-col gap-1.5 items-end">
                      <div className="flex items-center gap-1">
                        {card.changeType === 'positive' ? (
                          <IconTrendingDown
                            className="w-5 h-5 text-[#5927FF]"
                            stroke={1.5}
                          />
                        ) : (
                          <IconTrendingUp
                            className="w-5 h-5 text-[#F71111]"
                            stroke={1.5}
                          />
                        )}
                        <div
                          className={`text-sm font-normal leading-[16px] tracking-[0.5%] ${
                            card.changeType === 'positive'
                              ? 'text-[#5927FF]'
                              : 'text-[#F71111]'
                          }`}>
                          {card.change}
                        </div>
                      </div>
                      <div className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                        in 90 days
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
  )
}


