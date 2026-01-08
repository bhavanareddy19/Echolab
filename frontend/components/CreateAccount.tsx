'use client';

import { IconCircleCheckFilled } from '@tabler/icons-react';
import DropdownInput from './UI/DropdownInput';
import InputField from '@/components/UI/InputField';
import ConfirmationDialog from './UI/ConfirmationDialog';
import { useState } from 'react';
import { signUp } from '@/actions/auth';
import { useRouter } from 'next/navigation';

export default function CreateAccount() {
  const [currentStep, setCurrentStep] = useState(1);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [role, setRole] = useState('');
  const [dataRange, setDataRange] = useState('30-days');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  const router = useRouter();

  const handleSubmit = async () => {
    // Validate step 1 fields
    const newErrors: { [key: string]: string } = {};
    if (!email.trim()) newErrors.email = 'Email is required';
    if (!password.trim()) newErrors.password = 'Password is required';
    if (!confirmPassword.trim())
      newErrors.confirmPassword = 'Confirm password is required';
    if (password !== confirmPassword)
      newErrors.confirmPassword = 'Passwords do not match';
    if (!firstName.trim()) newErrors.firstName = 'First name is required';
    if (!lastName.trim()) newErrors.lastName = 'Last name is required';
    if (!companyName.trim()) newErrors.companyName = 'Company name is required';
    if (!role.trim()) newErrors.role = 'Role is required';

    if (Object.keys(newErrors).length === 0) {
      setErrors({});
      setCurrentStep(2);

      const formData = new FormData();
      formData.append('email', email);
      formData.append('password', password);
      formData.append('firstName', firstName);
      formData.append('lastName', lastName);
      formData.append('companyName', companyName);
      formData.append('role', role);

      // API call to create user

      // const { status } = await signUp(formData);
      // if (status === 'User created successfully') {
      //   router.push('/');
      // } else {
      //   setErrors({
      //     email: status,
      //   });
      // }
    } else {
      setErrors(newErrors);
    }
  };


  const handleConnectZendesk = async () => {
    // API call to connect Zendesk (get Zendesk credentials)

    if (!isConnecting && !isConnected) {
      setIsConnecting(true);
      // Simulate API call
      setTimeout(() => {
        setIsConnecting(false);
        setIsConnected(true);
        setTimeout(() => {
          setCurrentStep(3);
        }, 2000);
      }, 5000);
    }
  };

  const handleStartSync = async () => {
    // API call to start sync (import data from Zendesk)

    setCurrentStep(3);
  };

  return (
    <div className="w-full flex justify-center items-center min-h-[calc(100vh-120px)]">
      <div className="w-96 lg:w-[560px] flex flex-col items-center justify-center gap-5">
        {currentStep === 1 ? (
          <>
            <div className="w-full flex flex-col items-start justify-start gap-2.5">
              <p className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
                Create Account
              </p>
              <p className="font-normal text-xs tracking-[0.5%] leading-[14px] text-black">
                All fields are required.
              </p>
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-1.5">
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Create Username
              </div>
              <InputField
                placeholder="email@domain.com"
                value={email}
                onValueChange={setEmail}
                className={errors.email ? 'border-red-500' : ''}
                onFocus={() => {
                  if (errors.email) {
                    setErrors((prev) => ({ ...prev, email: '' }));
                  }
                }}
              />
              {errors.email && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.email}
                </div>
              )}
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-1.5">
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Create Password
              </div>
              <InputField
                placeholder="Password"
                value={password}
                onValueChange={setPassword}
                type="password"
                className={
                  errors.password
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : ''
                }
                onFocus={() => {
                  if (errors.password) {
                    setErrors((prev) => ({ ...prev, password: '' }));
                  }
                }}
              />
              {errors.password && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.password}
                </div>
              )}
              <InputField
                placeholder="Confirm Password"
                value={confirmPassword}
                onValueChange={setConfirmPassword}
                type="password"
                className={
                  errors.confirmPassword
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : ''
                }
                onFocus={() => {
                  if (errors.confirmPassword) {
                    setErrors((prev) => ({ ...prev, confirmPassword: '' }));
                  }
                }}
              />
              {errors.confirmPassword && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.confirmPassword}
                </div>
              )}
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-1.5">
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                First Name
              </div>
              <InputField
                placeholder="First Name"
                value={firstName}
                onValueChange={setFirstName}
                className={
                  errors.firstName
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : ''
                }
                onFocus={() => {
                  if (errors.firstName) {
                    setErrors((prev) => ({ ...prev, firstName: '' }));
                  }
                }}
              />
              {errors.firstName && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.firstName}
                </div>
              )}
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Last Name
              </div>
              <InputField
                placeholder="Last Name"
                value={lastName}
                onValueChange={setLastName}
                className={
                  errors.lastName
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : ''
                }
                onFocus={() => {
                  if (errors.lastName) {
                    setErrors((prev) => ({ ...prev, lastName: '' }));
                  }
                }}
              />
              {errors.lastName && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.lastName}
                </div>
              )}
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-1.5">
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Company Name
              </div>
              <InputField
                placeholder="Company Name"
                value={companyName}
                onValueChange={setCompanyName}
                className={
                  errors.companyName
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : ''
                }
                onFocus={() => {
                  if (errors.companyName) {
                    setErrors((prev) => ({ ...prev, companyName: '' }));
                  }
                }}
              />
              {errors.companyName && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.companyName}
                </div>
              )}
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Role in Company
              </div>
              <InputField
                placeholder="Role"
                value={role}
                onValueChange={setRole}
                className={
                  errors.role
                    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
                    : ''
                }
                onFocus={() => {
                  if (errors.role) {
                    setErrors((prev) => ({ ...prev, role: '' }));
                  }
                }}
              />
              {errors.role && (
                <div className="text-red-500 text-xs font-medium">
                  {errors.role}
                </div>
              )}
            </div>

            <div className="w-full flex items-center justify-center gap-2.5">
              <div
                onClick={() => setShowCancelDialog(true)}
                className="py-2 px-3 tracking-[0.5%] leading-[16px] rounded-lg font-medium text-sm cursor-pointer w-18 text-center text-black bg-primary transition-transform duration-200 hover:scale-105">
                Cancel
              </div>
              <div
                onClick={async () => {
                  await handleSubmit();
                }}
                className="py-2 px-3 tracking-[0.5%] leading-[16px] rounded-lg font-medium text-sm cursor-pointer w-18 text-center text-white brand-gradient transition-transform duration-200 hover:scale-105">
                Next
              </div>
            </div>
          </>
        ) : currentStep === 2 ? (
          <div className="w-full flex flex-col items-start justify-start gap-10">
            <div className="w-full flex flex-col items-start justify-start gap-2.5">
              <div className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
                Get Started
              </div>
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Connect your Zendesk instance to analyze customer support
                tickets.
              </div>
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-2.5">
              <p className="font-bold text-[10px] tracking-[0.5%] leading-[10px] text-black">
                Step 1/2
              </p>
              <div className="w-full flex items-center justify-start gap-2">
                <div className="w-full h-1 brand-gradient" />
                <div className="w-full h-1 bg-[#8C8C8C]" />
              </div>
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-5 bg-primary rounded-[10px] p-5">
              <div className="w-full flex flex-col items-start justify-start gap-2.5">
                <p className="font-semibold text-sm tracking-[0.5%] leading-[16px] text-black">
                  We are ready to connect
                </p>
                <p className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                  We&apos;ll securely connect to your Zendesk instance to access
                  support tickets and customer feedback.
                </p>
              </div>
              <div
                onClick={() => {
                  handleConnectZendesk();
                }}
                className={`text-white text-sm font-medium tracking-[0.5%] leading-[16px] rounded-lg px-3 py-2.5 w-full text-center transition-transform duration-200 ${
                  isConnected
                    ? ''
                    : 'brand-gradient cursor-pointer hover:scale-102'
                }`}>
                {isConnecting ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  </div>
                ) : isConnected ? (
                  <div className="flex items-center justify-center gap-2">
                    <IconCircleCheckFilled fill="#0CB500" />
                    <span className="text-[#0CB500] font-bold text-sm tracking-[0.5%] leading-[16px]">
                      Connected Successfully
                    </span>
                  </div>
                ) : (
                  'Connect Zendesk'
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full flex flex-col items-start justify-start gap-10">
            <div className="w-full flex flex-col items-start justify-start gap-2.5">
              <div className="font-semibold text-2xl tracking-[0.5%] leading-[26px] text-black">
                Connect Zendesk
              </div>
              <div className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                Enter your Zendesk credentials to complete the setup.
              </div>
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-2.5">
              <p className="font-bold text-[10px] tracking-[0.5%] leading-[10px] text-black">
                Step 2/2
              </p>
              <div className="w-full flex items-center justify-start gap-2">
                <div className="w-full h-1 brand-gradient" />
                <div className="w-full h-1 brand-gradient" />
              </div>
            </div>

            <div className="w-full flex flex-col items-start justify-start gap-5 bg-primary rounded-[10px] p-5">
              <div className="w-full flex flex-col items-start justify-start gap-2.5">
                <p className="font-semibold text-sm tracking-[0.5%] leading-[16px] text-black">
                  Select Data Range
                </p>
                <p className="font-normal text-sm tracking-[0.5%] leading-[16px] text-black">
                  Choose how far back you would like us to analyze your support
                  tickets.
                </p>
              </div>
              <div className="w-full flex flex-col items-center justify-start gap-2.5">
                <DropdownInput
                  value={dataRange}
                  onChange={setDataRange}
                  options={[
                    { value: '30-days', label: 'Last 30 days (Recommended)' },
                    { value: '90-days', label: 'Last 90 days' },
                    { value: '6-months', label: 'Last 6 months' },
                    { value: '12-months', label: 'Last 12 months' },
                  ]}
                />
                <div className="w-full bg-[#F6F6F6] px-2.5 py-3 rounded-[8px] font-normal text-xs tracking-[0.5%] leading-[14px] text-[#7F7F7F]">
                  Estimated: ~2,847 tickets to analyze from the last 90 days
                </div>
              </div>
            </div>

            <div
              onClick={() => handleStartSync()}
              className="brand-gradient text-white text-sm font-medium tracking-[0.5%] leading-[16px] rounded-lg px-3 py-2.5 w-full text-center cursor-pointer transition-transform duration-200 hover:scale-102">
              Start Sync
            </div>
          </div>
        )}
      </div>

      <ConfirmationDialog
        isOpen={showCancelDialog}
        onCancel={() => setShowCancelDialog(false)}
        onConfirm={() => {
          setShowCancelDialog(false);
          window.history.back();
        }}
        title="Leave this page?"
        message="You haven’t finished creating your account. Leaving now will erase all entered details. Are you sure you want to proceed?"
        cancelText="Cancel"
        confirmText="Leave"
      />
    </div>
  );
}
