import React from 'react';
import { FileText } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ 
  title = "No items found", 
  description = "Get started by adding your first item",
  icon,
  action
}) => {
  return (
    <div className="text-center py-12">
      <div className="mx-auto h-12 w-12 text-gray-400 mb-4 flex items-center justify-center">
        {icon || <FileText className="h-12 w-12 text-gray-400" />}
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      <p className="text-gray-500 mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};