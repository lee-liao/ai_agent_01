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
  data: RefusalData;
}

export function RefusalMessage({ data }: RefusalMessageProps) {
  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4 shadow-sm">
      {/* Empathy statement - prominent and warm */}
      <p className="font-semibold text-amber-900 mb-2 text-base" data-testid="refusal-empathy">
        {data.empathy}
      </p>
      
      {/* Explanation message */}
      <p className="text-gray-700 mb-4 leading-relaxed">
        {data.message}
      </p>
      
      {/* Resource links */}
      {data.resources && data.resources.length > 0 && (
        <div className="space-y-2">
          {data.resources.map((resource, index) => (
            <a
              key={index}
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="refusal-resource"
              className="
                block w-full
                bg-amber-600 hover:bg-amber-700
                text-white font-medium
                px-4 py-2.5 rounded-md
                transition-colors duration-200
                text-center
                focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
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

