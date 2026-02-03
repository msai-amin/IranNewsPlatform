'use client';

import { CheckCircle, AlertTriangle, AlertCircle, Clock } from 'lucide-react';

interface StatusBadgeProps {
  status: string | null;
  size?: 'sm' | 'md' | 'lg';
}

export default function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const normalizedStatus = status?.toLowerCase() || 'pending';
  
  const configs: Record<string, { 
    label: string; 
    bgColor: string; 
    textColor: string;
    borderColor: string;
    icon: React.ReactNode 
  }> = {
    verified: {
      label: 'Verified',
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
      borderColor: 'border-green-200',
      icon: <CheckCircle className={size === 'lg' ? 'w-5 h-5' : size === 'md' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />,
    },
    unverified: {
      label: 'Unverified',
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-700',
      borderColor: 'border-amber-200',
      icon: <AlertCircle className={size === 'lg' ? 'w-5 h-5' : size === 'md' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />,
    },
    propaganda: {
      label: 'Propaganda',
      bgColor: 'bg-red-50',
      textColor: 'text-red-700',
      borderColor: 'border-red-200',
      icon: <AlertTriangle className={size === 'lg' ? 'w-5 h-5' : size === 'md' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />,
    },
    pending: {
      label: 'Pending',
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-600',
      borderColor: 'border-gray-200',
      icon: <Clock className={size === 'lg' ? 'w-5 h-5' : size === 'md' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />,
    },
  };
  
  const config = configs[normalizedStatus] || configs.pending;
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  };
  
  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${config.bgColor} ${config.textColor} ${config.borderColor} ${sizeClasses[size]}`}>
      {config.icon}
      {config.label}
    </span>
  );
}
