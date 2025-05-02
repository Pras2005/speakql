import React from "react";
import { motion } from "framer-motion";

interface FooterLink {
  label: string;
  href: string;
}

interface FooterColumnProps {
  title: string;
  links: FooterLink[];
  delay?: number;
}

const FooterColumn: React.FC<FooterColumnProps> = ({
  title,
  links,
  delay = 0,
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.8, delay }}
  >
    <div className="text-indigo-300 font-bold mb-3">{title}</div>
    <ul>
      {links.map((link) => (
        <li key={link.label} className="mb-2">
          <a
            href={link.href}
            className="text-gray-400 hover:text-white transition-colors text-sm"
            target="_blank"
            rel="noopener noreferrer"
          >
            {link.label}
          </a>
        </li>
      ))}
    </ul>
  </motion.div>
);

export default FooterColumn;

