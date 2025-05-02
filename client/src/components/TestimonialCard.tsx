import React from "react";
import { motion } from "framer-motion";
import { Star } from "lucide-react";

interface TestimonialCardProps {
  quote: string;
  author: string;
  role: string;
  rating?: number;
  delay?: number;
  isVisible?: boolean;
}

const TestimonialCard: React.FC<TestimonialCardProps> = ({
  quote,
  author,
  role,
  rating = 5,
  delay = 0,
  isVisible = true,
}) => (
  <motion.div
    className="bg-gray-800 rounded-xl p-8 border border-gray-700 shadow-lg flex flex-col"
    initial={{ opacity: 0, y: 40 }}
    animate={isVisible ? { opacity: 1, y: 0 } : {}}
    transition={{ duration: 0.7, delay }}
  >
    <div className="mb-4 text-yellow-400 flex">
      {[...Array(rating)].map((_, i) => (
        <Star key={i} className="w-5 h-5" fill="currentColor" />
      ))}
    </div>
    <blockquote className="text-lg text-white italic mb-4">"{quote}"</blockquote>
    <div className="text-indigo-300 font-semibold">{author}</div>
    <div className="text-gray-400 text-sm">{role}</div>
  </motion.div>
);

export default TestimonialCard;

