import { Info } from 'lucide-react';
import { useState } from 'react';

interface TooltipProps {
    content: string;
}

export const Tooltip: React.FC<TooltipProps> = ({ content }) => {
    const [show, setShow] = useState(false);

    return (
        <div className="relative inline-block ml-1">
            <Info
                size={16}
                className="text-gray-400 hover:text-primary cursor-help inline"
                onMouseEnter={() => setShow(true)}
                onMouseLeave={() => setShow(false)}
            />
            {show && (
                <div className="absolute z-50 w-64 p-3 text-sm bg-surface border border-primary/30 rounded-lg shadow-xl left-6 top-0 text-gray-200">
                    {content}
                </div>
            )}
        </div>
    );
};
