export default function Overview() {
  const dashboardCards = [
    {
      title: 'Ticket Analyzed',
      value: '2869',
      change: '+12% vs last month',
      changeType: 'positive' as const,
    },
    {
      title: 'Painpoints',
      value: '123',
      change: '-12% vs last month',
      changeType: 'negative' as const,
    },
    {
      title: 'Hypothesis Generated',
      value: '12',
      change: '+12% vs last month',
      changeType: 'positive' as const,
    },
    {
      title: 'Experiments Created',
      value: '56',
      subtitle: 'out of 123 active tickets',
      change: '+12% vs last month',
      changeType: 'positive' as const,
    },
  ];

  const getChangeStyles = (changeType: 'positive' | 'negative') => {
    return changeType === 'positive'
      ? 'rounded-[8px] border border-success bg-success p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-success'
      : 'rounded-[8px] border border-unconnected bg-unconnected p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-unconnected';
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
        Overview
      </div>
      <div className="col-span-12">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 xl:grid-cols-4">
          {dashboardCards.map((card, index) => (
            <div
              key={index}
              className="flex flex-col justify-between rounded-[8px] bg-white px-3.5 py-4 gap-5">
              <div className="flex flex-col gap-5">
                <div className="text-[#7F7F7F] text-sm tracking-[0.5%] leading-[16px] font-semibold">
                  {card.title}
                </div>
                <div className="flex flex-col gap-1.5">
                  <div className="text-2xl font-semibold text-black leading-[26px] tracking-[0.5%]">
                    {card.value}
                  </div>
                  {card.subtitle && (
                    <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                      {card.subtitle}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-start gap-1">
                <span className={getChangeStyles(card.changeType)}>
                  {card.change}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
