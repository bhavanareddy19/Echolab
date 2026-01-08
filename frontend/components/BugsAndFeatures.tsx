
export default function BugsAndFeatures() {
  return (
    <div className="flex flex-col gap-5">
          <div className="text-black text-xl font-semibold leading-[22px] tracking-[0.5%]">
            Bugs and Features
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Features */}
            <div className="w-full flex justify-between items-center bg-primary rounded-[8px] py-4 px-3">
              <div className="flex flex-col gap-10">
                <p className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
                  Features
                </p>
                <div className="rounded-[8px] border border-success bg-success p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-success">
                  +12% vs last month
                </div>
              </div>
              <div className="flex flex-row items-center justify-between gap-4 ">
                <div className="flex flex-col gap-1.5">
                  <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                    56
                  </p>
                  <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                    in 90 days
                  </p>
                </div>
                <div className="w-[1px] h-12 bg-[#E8E8E8]" />
                <div className="flex flex-col gap-1.5">
                  <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                    19
                  </p>
                  <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                    in progress
                  </p>
                </div>
                <div className="w-[1px] h-12 bg-[#E8E8E8]" />
                <div className="flex flex-col gap-1.5">
                  <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                    37
                  </p>
                  <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                    awaiting
                  </p>
                </div>
              </div>
            </div>

            {/* Bugs */}
            <div className="w-full flex justify-between items-center bg-primary rounded-[8px] py-4 px-3">
              <div className="flex flex-col gap-10">
                <p className="text-[#7F7F7F] text-sm font-semibold leading-[16px] tracking-[0.5%]">
                  Bugs
                </p>
                <div className="rounded-[8px] border border-[#FFDCDC] bg-[#FFF2F2] p-1.5 text-[10px] leading-[12px] tracking-[0.5%] font-medium text-[#F71111]">
                  -8% vs last month
                </div>
              </div>
              <div className="flex flex-row items-center justify-between gap-4 ">
                <div className="flex flex-col gap-1.5">
                  <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                    34
                  </p>
                  <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                    in 90 days
                  </p>
                </div>
                <div className="w-[1px] h-12 bg-[#E8E8E8]" />
                <div className="flex flex-col gap-1.5">
                  <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                    12
                  </p>
                  <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                    in progress
                  </p>
                </div>
                <div className="w-[1px] h-12 bg-[#E8E8E8]" />
                <div className="flex flex-col gap-1.5">
                  <p className="text-black text-2xl font-semibold leading-[26px] tracking-[0.5%]">
                    22
                  </p>
                  <p className="text-[#7F7F7F] text-xs tracking-[0.5%] leading-[14px] font-normal">
                    awaiting
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
  )
}

