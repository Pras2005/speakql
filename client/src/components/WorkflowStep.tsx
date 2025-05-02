import React from "react";
import { motion } from "framer-motion";

interface WorkflowStepProps {
  number: string;
  title: string;
  description: string;
  delay?: number;
  isVisible?: boolean;
}

const WorkflowStep: React.FC<WorkflowStepProps> = ({
  number,
  title,
  description,
  delay = 0,
  isVisible = true,
}) => (
  <motion.div
    className="bg-gray-900 rounded-xl p-8 border border-indigo-800 flex flex-col items-center text-center shadow-lg"
    initial={{ opacity: 0, y: 40 }}
    animate={isVisible ? { opacity: 1, y: 0 } : {}}
    transition={{ duration: 0.7, delay }}
  >
    <div className="text-2xl font-bold text-indigo-400 mb-2">{number}</div>
    <h4 className="text-lg font-semibold text-white mb-2">{title}</h4>
    <p className="text-gray-400 text-sm">{description}</p>
  </motion.div>
);

export default WorkflowStep;

