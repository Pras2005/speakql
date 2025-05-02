import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface StatCounterProps {
  label: string;
  value: number;
  suffix?: string;
  icon?: React.ReactNode;
  delay?: number;
  isVisible?: boolean;
}

const StatCounter: React.FC<StatCounterProps> = ({
  label,
  value,
  suffix = "",
  icon,
  delay = 0,
  isVisible = true,
}) => {
  const [displayed, setDisplayed] = useState(0);

  useEffect(() => {
    if (!isVisible) return;
    let start = 0;
    const duration = 800;
    const increment = value / (duration / 16);
    let raf: number;
    const animate = () => {
      start += increment;
      if (start < value) {
        setDisplayed(Math.floor(start));
        raf = requestAnimationFrame(animate);
      } else {
        setDisplayed(value);
      }
    };
    animate();
    return () => cancelAnimationFrame(raf);
  }, [isVisible, value]);

  return (
    <motion.div
      className="flex flex-col items-center bg-gray-800 rounded-xl p-6 border border-gray-700"
      initial={{ opacity: 0, y: 30 }}
      animate={isVisible ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay }}
    >
      <div className="mb-2 text-indigo-400">{icon}</div>
      <div className="text-2xl font-bold text-white">
        {displayed}
        {suffix}
      </div>
      <div className="text-gray-400 text-sm">{label}</div>
    </motion.div>
  );
};

export default StatCounter;

