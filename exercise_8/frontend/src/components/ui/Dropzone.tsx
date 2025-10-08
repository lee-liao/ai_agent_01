import React, { useCallback } from 'react';
import { useDropzone, DropzoneOptions, FileRejection } from 'react-dropzone';
import { Upload } from 'lucide-react';

interface DropzoneProps extends DropzoneOptions {
  label?: string;
  description?: string;
  onDropCallback?: (acceptedFiles: File[], fileRejections: FileRejection[]) => void;
}

export const Dropzone: React.FC<DropzoneProps> = ({ 
  label = "Upload Documents", 
  description = "Drag & drop files here, or click to select", 
  onDropCallback,
  ...dropzoneOptions
}) => {
  const onDrop = useCallback((acceptedFiles: File[], fileRejections: FileRejection[]) => {
    if (onDropCallback) {
      onDropCallback(acceptedFiles, fileRejections);
    }
  }, [onDropCallback]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    ...dropzoneOptions
  });

  return (
    <div 
      {...getRootProps()} 
      className={`
        border-2 border-dashed rounded-lg cursor-pointer transition-all 
        ${isDragActive 
          ? "border-primary-500 bg-primary-50" 
          : "border-gray-300 hover:border-primary-400 hover:bg-gray-50"
        }
      `}
    >
      <input {...getInputProps()} />
      <div className="text-center py-8">
        <Upload
          className={`
            mx-auto h-12 w-12 mb-4 
            ${isDragActive ? "text-primary-600" : "text-gray-400"}
          `}
        />
        {isDragActive ? (
          <p className="text-lg text-primary-600 font-medium">
            Drop the files here...
          </p>
        ) : (
          <>
            <p className="text-lg text-gray-700 mb-2">
              {label}
            </p>
            <p className="text-sm text-gray-500">
              {description}
            </p>
          </>
        )}
      </div>
    </div>
  );
};