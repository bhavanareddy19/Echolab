'use client';

import { Checkbox } from '@/components/UI/checkbox';
import { RiLightbulbFlashLine } from 'react-icons/ri';
import { useState, useEffect } from 'react';
import EditControls from './EditControls';
import TextArea from './TextArea';
import DropdownInput from './DropdownInput';
import { IconExternalLink } from '@tabler/icons-react';
import { useEditMode } from '@/contexts/EditModeContext';
import { HypothesisContainerProps } from '@/types';

export default function HypothesisContainer({
  hypothesis,
  title,
  primaryMetric,
  secondaryMetric,
  impactPercentage,
  impactLevel,
  inspiration,
  onHypothesisChange,
}: HypothesisContainerProps) {
  const [selectedMetric, setSelectedMetric] = useState(primaryMetric);
  const [selectedSecondaryMetric, setSelectedSecondaryMetric] =
    useState(secondaryMetric);
  const { setIsEditing } = useEditMode();

  const metrics = [
    { value: 'conversion-rate', label: 'Conversion Rate' },
    { value: 'completion-rate', label: 'Completion Rate' },
    { value: 'time-to-completion', label: 'Time to Completion' },
    { value: 'cart-abandonment', label: 'Cart Abandonment' },
    { value: 'user-satisfaction', label: 'User Satisfaction' },
    { value: 'return-visits', label: 'Return Visits' },
    { value: 'page-load-time', label: 'Page Load Time' },
    { value: 'support-tickets', label: 'Support Tickets' },
    { value: 'user-engagement', label: 'User Engagement' },
    { value: 'feature-adoption', label: 'Feature Adoption' },
  ];

  const isAnyFieldInEditMode = Object.values(hypothesis.editMode).some(Boolean);

  useEffect(() => {
    setIsEditing(isAnyFieldInEditMode);
  }, [isAnyFieldInEditMode, setIsEditing]);

  const onEdit = (field: 'if' | 'then' | 'variantA' | 'variantB') => {
    const updatedHypothesis = {
      ...hypothesis,
      editMode: {
        ...hypothesis.editMode,
        [field]: true,
      },
      temp: {
        ...hypothesis.temp,
        [field]: hypothesis.current[field],
      },
    };
    onHypothesisChange(updatedHypothesis);
  };

  const onCancel = (field: 'if' | 'then' | 'variantA' | 'variantB') => {
    const updatedHypothesis = {
      ...hypothesis,
      editMode: {
        ...hypothesis.editMode,
        [field]: false,
      },
    };
    onHypothesisChange(updatedHypothesis);
  };

  const onSave = (field: 'if' | 'then' | 'variantA' | 'variantB') => {
    const updatedHypothesis = {
      ...hypothesis,
      editMode: {
        ...hypothesis.editMode,
        [field]: false,
      },
      current: {
        ...hypothesis.current,
        [field]: hypothesis.temp[field],
      },
    };
    onHypothesisChange(updatedHypothesis);
  };

  const handleChange = (
    field: 'if' | 'then' | 'variantA' | 'variantB',
    value: string
  ) => {
    const updatedHypothesis = {
      ...hypothesis,
      temp: {
        ...hypothesis.temp,
        [field]: value,
      },
    };
    onHypothesisChange(updatedHypothesis);
  };

  const handleCheckboxChange = (checked: boolean) => {
    const updatedHypothesis = {
      ...hypothesis,
      checked,
    };
    onHypothesisChange(updatedHypothesis);
  };

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'High':
        return 'bg-success border-success text-success';
      case 'Medium':
        return 'bg-[#FFFBE3] border-[#FFE4B6] text-[#F09800]';
      case 'Low':
        return 'bg-[#FFF2F2] border-[#FFDCDC] text-[#F71111]';
      default:
        return 'bg-success border-success text-success';
    }
  };

  return (
    <div className="bg-primary p-4 rounded-xl flex flex-col gap-7.5">
      <div className="flex justify-between items-center">
        <div className="flex gap-2 justify-center items-center">
          <Checkbox
            checked={hypothesis.checked}
            onCheckedChange={(value) => handleCheckboxChange(!!value)}
            className="data-[state=checked]:border-[#6750a4] data-[state=checked]:bg-[#6750a4] data-[state=checked]:text-white rounded-xs border-[1.5px] border-[#7F7F7F]"
          />
          <p className="font-semibold text-xl tracking-[0.5%] leading-[22px]">
            {title}
          </p>
        </div>
        <div
          className={`py-2.5 px-3 font-medium text-sm tracking-[0.5%] leading-[16px] rounded-lg transition-colors duration-200 border ${
            hypothesis.checked
              ? 'border-brand-color text-[#5927ff] bg-[#F1F3FF]'
              : 'disabled-brand-color text-neutral-200 border-[#BEC2E5]'
          }`}>
          Push to GrowthBook
        </div>
      </div>

      <div className="flex justify-between items-center bg-secondary px-3 py-4 rounded-[12px] gap-5">
        <div className="flex items-center gap-3 w-full">
          <div className="self-start pt-1">
            <RiLightbulbFlashLine className="w-4.5 h-4.5" />
          </div>
          <div className="flex flex-col w-full gap-1.5">
            {/* IF Row */}
            <div className="flex gap-2.5 items-center">
              <div className="font-semibold text-[16px] w-[50px] tracking-[0.5%] leading-[18px] text-[#5927FF]">
                IF
              </div>
              <TextArea
                hypothesis={hypothesis}
                handleChange={handleChange}
                field="if"
              />
            </div>

            {/* THEN Row */}
            <div className="flex gap-2.5 items-center">
              <div className="font-semibold text-[16px] w-[50px] tracking-[0.5%] leading-[18px] text-[#5927FF]">
                THEN
              </div>
              <TextArea
                hypothesis={hypothesis}
                handleChange={handleChange}
                field="then"
              />
            </div>
          </div>
        </div>

        {/* Edit/Save Controls */}
        <EditControls
          onSave={() => {
            const updatedHypothesis = {
              ...hypothesis,
              editMode: {
                ...hypothesis.editMode,
                if: false,
                then: false,
              },
              current: {
                ...hypothesis.current,
                if: hypothesis.temp.if,
                then: hypothesis.temp.then,
              },
            };
            onHypothesisChange(updatedHypothesis);
          }}
          onCancel={() => {
            const updatedHypothesis = {
              ...hypothesis,
              editMode: {
                ...hypothesis.editMode,
                if: false,
                then: false,
              },
            };
            onHypothesisChange(updatedHypothesis);
          }}
          onEdit={() => {
            const updatedHypothesis = {
              ...hypothesis,
              editMode: {
                ...hypothesis.editMode,
                if: true,
                then: true,
              },
              temp: {
                ...hypothesis.temp,
                if: hypothesis.current.if,
                then: hypothesis.current.then,
              },
            };
            onHypothesisChange(updatedHypothesis);
          }}
          editMode={hypothesis.editMode.if || hypothesis.editMode.then}
          field="if"
        />
      </div>

      <div className="flex flex-col gap-4">
        <div className="font-semibold text-[16px] tracking-[0.5%] leading-[16px]">
          Variants
        </div>
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between py-1 px-3 bg-[#F6F6F6] rounded-[12px] gap-5">
            <div className="flex gap-1.5 items-center w-full">
              <div className="bg-[#E8E8E8] font-bold text-xs tracking-[0.5%] leading-[16px] rounded-[6px] w-6 h-6 flex items-center justify-center">
                A
              </div>
              <TextArea
                hypothesis={hypothesis}
                handleChange={handleChange}
                field="variantA"
              />
            </div>
            <div>
              <EditControls
                onSave={() => onSave('variantA')}
                onCancel={() => onCancel('variantA')}
                onEdit={() => onEdit('variantA')}
                editMode={hypothesis.editMode.variantA}
                field="variantA"
              />
            </div>
          </div>

          <div className="flex items-center justify-between py-1 px-3 bg-[#F6F6F6] rounded-[12px] gap-3">
            <div className="flex gap-1.5 items-center w-full">
              <div className="bg-[#E8E8E8] font-bold text-xs tracking-[0.5%] leading-[16px] rounded-[6px] w-6 h-6 flex items-center justify-center">
                B
              </div>
              <TextArea
                hypothesis={hypothesis}
                handleChange={handleChange}
                field="variantB"
              />
            </div>
            <div>
              <EditControls
                onSave={() => onSave('variantB')}
                onCancel={() => onCancel('variantB')}
                onEdit={() => onEdit('variantB')}
                editMode={hypothesis.editMode.variantB}
                field="variantB"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="w-full flex gap-4">
        <DropdownInput
          label="Primary Metric"
          value={selectedMetric}
          onChange={setSelectedMetric}
          options={metrics}
        />

        <DropdownInput
          label="Secondary Metric"
          value={selectedSecondaryMetric}
          onChange={setSelectedSecondaryMetric}
          options={metrics}
        />
      </div>

      <div className="flex flex-col gap-4 w-1/2">
        <div className="flex justify-between items-center">
          <div className="font-semibold text-[16px] tracking-[0.5%] leading-[18px]">
            Impact Estimates
          </div>
          <div className="flex items-center gap-1">
            <div className="font-normal text-[14px] tracking-[0.5%] leading-[16px]">
              {impactPercentage}%
            </div>
            <div
              className={`flex items-center border rounded-[8px] p-1.5 gap-1.5 w-fit ${getImpactColor(
                impactLevel
              )}`}>
              <div
                className={`text-[10px] font-medium tracking-[0.5%] leading-2.5`}>
                {impactLevel}
              </div>
            </div>
          </div>
        </div>
        <div className="w-full h-1.5 bg-[#E8E8E8] rounded-full">
          <div
            className="brand-gradient h-full rounded-full"
            style={{ width: `${impactPercentage}%` }}
          />
        </div>
      </div>

      <div className="py-4 px-3 bg-secondary rounded-[12px]">
        <div className="flex flex-col gap-4">
          <div className="font-semibold text-[16px] tracking-[0.5%] leading-[18px]">
            Inspiration
          </div>
          <div className="flex items-center gap-1 font-normal text-[14px] tracking-[0.5%] leading-[16px]">
            {inspiration}
            <span className="cursor-pointer">
              <IconExternalLink className="w-4 h-4 text-[#8C8C8C]" />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
