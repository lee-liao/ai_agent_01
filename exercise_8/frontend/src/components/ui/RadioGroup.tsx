
import React from 'react';
import { clsx } from 'clsx';

interface RadioGroupOption<T extends string> {
  value: T;
  label: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
}

interface RadioGroupProps<T extends string> {
  name: string;
  options: RadioGroupOption<T>[];
  selectedValue: T;
  onChange: (value: T) => void;
}

export function RadioGroup<T extends string>({ name, options, selectedValue, onChange }: RadioGroupProps<T>) {
  return (
    <div className="grid grid-cols-1 gap-3">
      {options.map((option) => (
        <label
          key={option.value}
          className={clsx(
            'flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all',
            selectedValue === option.value
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
          )}
        >
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={selectedValue === option.value}
            onChange={(e) => onChange(e.target.value as T)}
            className="mt-1 mr-3"
          />
          {option.icon && <div className="mr-3">{option.icon}</div>}
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{option.label}</p>
            {option.description && (
              <p className="text-sm text-gray-600 mt-1">{option.description}</p>
            )}
          </div>
        </label>
      ))}
    </div>
  );
}
