/**
 * RefusalMessage component
 * Displays out-of-scope refusals with empathy, explanation, and resource links
 */

interface Resource {
  text: string;
  url: string;
}

interface RefusalData {
  empathy: string;
  message: string;
  resources: Resource[];
}

interface RefusalMessageProps {
  data: RefusalData | null;
}

export function RefusalMessage({ data }: RefusalMessageProps) {
  // Safety check: if data is null, show a default message
  if (!data) {
    return (
      <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4 shadow-sm">
        <p className="font-semibold text-amber-900 mb-2 text-base">
          Thank you for reaching out.
        </p>
        <p className="text-gray-700 mb-4 leading-relaxed">
          I'm not able to help with that specific question. Please consult a professional for guidance.
        </p>
      </div>
    );
  }

  return (
    <div 
      className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4 shadow-sm"
      role="alert"
      aria-live="polite"
      aria-label="Important message"
    >
      {/* Empathy statement - prominent and warm */}
      <p className="font-semibold text-amber-900 mb-2 text-base" data-testid="refusal-empathy" role="heading" aria-level={3}>
        {data.empathy}
      </p>
      
      {/* Explanation message */}
      <p className="text-gray-700 mb-4 leading-relaxed">
        {data.message}
      </p>
      
      {/* Resource links */}
      {data.resources && data.resources.length > 0 && (
        <div className="space-y-2" role="list" aria-label="Helpful resources">
          {data.resources.map((resource, index) => (
            <a
              key={index}
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="refusal-resource"
              aria-label={`${resource.text} - Opens in new tab`}
              className="
                block w-full
                bg-amber-600 hover:bg-amber-700
                text-white font-medium
                px-4 py-2.5 rounded-md
                transition-colors duration-200
                text-center
                focus:outline-2 focus:outline-white focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
              "
            >
              {resource.text} →
            </a>
          ))}
        </div>
      )}
      
      {/* Safety footer */}
      <p className="text-xs text-gray-500 mt-4 italic">
        This response is for your safety. Professional guidance is recommended for this type of concern.
      </p>
    </div>
  );
}

