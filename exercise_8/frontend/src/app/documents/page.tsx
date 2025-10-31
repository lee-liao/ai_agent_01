"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Dropzone } from "@/components/ui/Dropzone";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileText, Upload, Trash2, Eye, Calendar, FileType } from "lucide-react";

interface Document {
  doc_id: string;
  name: string;
  uploaded_at?: string;
  size?: number;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      // Real API call
      const docsData = await api.listDocs();
      setDocs(docsData);
      setError(null);
    } catch (err) {
      setError("Failed to load documents");
      console.error(err);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    setUploading(true);
    setError(null);
    
    try {
      // Real API calls for each file
      const uploadPromises = acceptedFiles.map(async (file) => {
        try {
          const result = await api.uploadDoc(file);
          return {
            doc_id: result.doc_id,
            name: result.name,
            uploaded_at: new Date().toISOString(),
            size: file.size,
          };
        } catch (error) {
          console.error(`Failed to upload ${file.name}:`, error);
          throw error;
        }
      });
      
      const newDocs = await Promise.all(uploadPromises);
      setDocs(prevDocs => [...newDocs, ...prevDocs]);
      setError(null);
    } catch (err) {
      setError("Failed to upload document");
      console.error(err);
    }
    finally {
      setUploading(false);
    }
  }, []);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "Unknown";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Unknown";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <PageHeader
        title="Documents"
        description="Upload legal contracts for review. Supported formats: PDF, DOCX, DOC, MD, TXT"
      />

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Upload Area */}
      <div className="mb-8">
        <Dropzone
          label="Drag & drop documents here, or click to select"
          description="Supports PDF, DOCX, DOC, Markdown, and TXT files"
          onDropCallback={(acceptedFiles, fileRejections) => {
            if (fileRejections.length > 0) {
              setError(`Some files were rejected: ${fileRejections.map(r => r.file.name).join(', ')}`);
            }
            handleDrop(acceptedFiles);
          }}
          accept={{
            'text/markdown': ['.md'],
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/plain': ['.txt'],
          }}
          multiple={true}
          disabled={uploading}
        />
        {uploading && (
          <div className="mt-4 text-center">
            <p className="text-lg text-gray-600">Uploading...</p>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Uploaded Documents ({docs.length})
        </h2>
        
        {docs.length === 0 ? (
          <Card>
            <EmptyState
              title="No documents uploaded yet"
              description="Upload your first document to get started"
              icon={<FileText className="h-12 w-12 text-gray-400" />}
            />
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {docs.map((doc) => (
              <Card
                key={doc.doc_id}
                className="hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className="bg-primary-100 p-3 rounded-lg">
                      <FileText className="w-6 h-6 text-primary-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                        {doc.name}
                      </h3>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <div className="flex items-center">
                          <FileType className="w-4 h-4 mr-1" />
                          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                            {doc.doc_id}
                          </span>
                        </div>
                        {doc.uploaded_at && (
                          <div className="flex items-center">
                            <Calendar className="w-4 h-4 mr-1" />
                            {formatDate(doc.uploaded_at)}
                          </div>
                        )}
                        {doc.size && (
                          <div className="flex items-center">
                            <FileText className="w-4 h-4 mr-1" />
                            {formatFileSize(doc.size)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="View document"
                    >
                      <Eye className="w-5 h-5" />
                    </Button>
                    <Button
                      variant="danger"
                      size="icon"
                      title="Delete document"
                    >
                      <Trash2 className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
