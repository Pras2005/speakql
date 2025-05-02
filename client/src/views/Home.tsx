import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Database, MessageSquare, Code, ArrowRight, Terminal, CheckCircle, Brain, Zap, Shield, ChevronRight, Users, Medal, Star } from 'lucide-react';
import { motion } from 'framer-motion';

// Assume these components exist in your project:
import TypeWriter from '@/components/TypeWriter';
import FeatureCard from '@/components/FeatureCard';
import WorkflowStep from '@/components/WorkflowStep';
import StatCounter from '@/components/StatCounter';
import TestimonialCard from '@/components/TestimonialCard';
import FooterColumn from '@/components/FooterColumn';

const HomePage = () => {
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [isVisible, setIsVisible] = useState({});
  
  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    
    const setupIntersectionObserver = () => {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            setIsVisible(prev => ({
              ...prev,
              [entry.target.id]: entry.isIntersecting
            }));
          });
        },
        { threshold: 0.1 }
      );
      document.querySelectorAll('.observe-me').forEach(el => {
        if (el.id) {
          observer.observe(el);
        }
      });
    };
    
    window.addEventListener('scroll', handleScroll);
    setupIntersectionObserver();
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Floating animation for background elements
  const floatingAnimation = {
    y: [0, -10, 0],
    transition: {
      duration: 4,
      repeat: Infinity,
      repeatType: "reverse",
      ease: "easeInOut"
    }
  };
  
  // Parallax effect based on scroll
  const getParallaxY = (factor) => {
    return -scrollY * factor;
  };
  
  return (
    <div className="relative min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 overflow-hidden">
      {/* Enhanced 3D background pattern with parallax */}
      <div 
        className="absolute inset-0 overflow-hidden opacity-15"
        style={{ transform: `translateY(${getParallaxY(0.05)}px)` }}
      >
        <div className="absolute top-0 right-0 w-full h-full">
          <svg width="100%" height="100%" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="gridGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
              </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="none" />
            <path d="M0 0L50 50M100 0L0 100M150 0L0 150M200 0L0 200M250 0L0 250M300 0L0 300" 
                  stroke="url(#gridGradient)" strokeWidth="1" fill="none" />
            <path d="M0 0L50 50M100 0L0 100M150 0L0 150M200 0L0 200M250 0L0 250M300 0L0 300" 
                  stroke="url(#gridGradient)" strokeWidth="1" fill="none" transform="translate(100, 0)" />
          </svg>
        </div>
      </div>

      {/* Animated particles */}
      {[...Array(15)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-indigo-600 opacity-10"
          style={{
            width: Math.random() * 20 + 10,
            height: Math.random() * 20 + 10,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            filter: 'blur(8px)'
          }}
          animate={{
            y: [0, -30, 0],
            x: [0, Math.random() * 20 - 10, 0],
            opacity: [0.1, 0.2, 0.1]
          }}
          transition={{
            duration: Math.random() * 10 + 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      ))}

      {/* Content */}
      <div className="relative z-10">
        {/* Hero Section - Enhanced with 3D and animations */}
        <div className="flex flex-col items-center justify-center pt-24 pb-20 px-4">
          <motion.div
            className="flex items-center gap-3 mb-6"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <motion.div 
              className="bg-indigo-900 p-3 rounded-full shadow-lg shadow-indigo-900/30"
              whileHover={{ rotate: 15, scale: 1.1 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <Database className="text-indigo-300 w-10 h-10" />
            </motion.div>
            <motion.h1 
              className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 to-purple-300"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              style={{ textShadow: '0 0 40px rgba(129, 140, 248, 0.3)' }}
            >
              SpeakQL
            </motion.h1>
          </motion.div>
          
          <motion.p 
            className="text-xl text-gray-300 text-center max-w-2xl mb-10"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <span className="font-semibold">Databases that understand humans</span>, not humans learning SQL.
            <span className="block mt-2 font-light text-gray-400">The revolution in database interaction starts here.</span>
          </motion.p>
          
          <motion.div 
            className="flex flex-col sm:flex-row gap-4 mb-16"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
              <Button
                onClick={() => navigate('/login')}
                className="bg-gray-800 hover:bg-gray-700 text-gray-100 px-8 py-6 rounded-lg text-lg font-medium shadow-lg border border-gray-700 transition-all"
              >
                Login
              </Button>
            </motion.div>
            <motion.div 
              whileHover={{ scale: 1.05 }} 
              whileTap={{ scale: 0.98 }}
              className="relative"
            >
              <Button
                onClick={() => navigate('/signup')}
                className="bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white px-8 py-6 rounded-lg text-lg font-medium shadow-lg transition-all overflow-hidden"
              >
                <motion.div 
                  className="absolute inset-0 bg-gradient-to-r from-indigo-600/0 via-white/20 to-indigo-600/0"
                  initial={{ x: '-100%' }}
                  animate={{ x: '100%' }}
                  transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                />
                <span className="relative z-10 flex items-center">
                  Sign Up Free <ChevronRight className="ml-1 w-5 h-5" />
                </span>
              </Button>
            </motion.div>
          </motion.div>
        </div>

        {/* Demo Section with Terminal UI - Enhanced 3D visualization */}
        <div id="demo-section" className="max-w-4xl mx-auto py-10 px-4 observe-me">
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={isVisible['demo-section'] ? { y: 0, opacity: 1 } : {}}
            transition={{ duration: 0.8 }}
            className="bg-black rounded-xl shadow-2xl overflow-hidden border border-gray-800 transform hover:scale-[1.02] transition-all duration-300"
            style={{ 
              boxShadow: '0 25px 50px -12px rgba(79, 70, 229, 0.2)',
              perspective: '1000px'
            }}
          >
            {/* Terminal Header */}
            <div className="bg-gray-800 px-4 py-2 flex items-center gap-2">
              <motion.div whileHover={{ scale: 1.2 }} className="w-3 h-3 rounded-full bg-red-500"></motion.div>
              <motion.div whileHover={{ scale: 1.2 }} className="w-3 h-3 rounded-full bg-yellow-500"></motion.div>
              <motion.div whileHover={{ scale: 1.2 }} className="w-3 h-3 rounded-full bg-green-500"></motion.div>
              <div className="ml-4 text-gray-400 text-sm">SpeakQL Terminal</div>
            </div>
            
            {/* Terminal Content - Enhanced conversation with typing animation */}
            <div className="p-6">
              <motion.div 
                className="flex items-start gap-3 mb-4"
                initial={{ opacity: 0 }}
                animate={isVisible['demo-section'] ? { opacity: 1 } : {}}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <div className="mt-1">
                  <MessageSquare size={16} className="text-indigo-400" />
                </div>
                <div>
                  <div className="text-gray-500 text-xs mb-1">Human:</div>
                  <TypeWriter 
                    text="Show me all customers who spent more than $1000 last month" 
                    className="text-white font-medium"
                    speed={30}
                    startDelay={800}
                    startOnView={isVisible['demo-section']}
                  />
                </div>
              </motion.div>
              
              <motion.div 
                className="flex items-start gap-3 mb-4 pl-8"
                initial={{ opacity: 0 }}
                animate={isVisible['demo-section'] ? { opacity: 1 } : {}}
                transition={{ duration: 0.5, delay: 1.8 }}
              >
                <div className="mt-1">
                  <Brain size={16} className="text-green-400" />
                </div>
                <div>
                  <div className="text-gray-500 text-xs mb-1">SpeakQL thinking:</div>
                  <div className="text-gray-400 italic text-sm">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={isVisible['demo-section'] ? { width: '100%' } : {}}
                      transition={{ duration: 1, delay: 2 }}
                      className="h-0.5 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-full mb-1"
                    />
                    Translating natural language to database query...
                  </div>
                </div>
              </motion.div>
              
              <motion.div 
                className="bg-gray-900 p-4 rounded-md mb-4 border border-gray-800"
                initial={{ opacity: 0, rotateX: 20 }}
                animate={isVisible['demo-section'] ? { opacity: 1, rotateX: 0 } : {}}
                transition={{ duration: 0.5, delay: 2.5 }}
                style={{ transformOrigin: 'top' }}
              >
                <div className="text-blue-400 font-mono mb-2">// Generated SQL Query:</div>
                <TypeWriter 
                  text={`SELECT customers.name, SUM(orders.amount) as total_spent
FROM customers
JOIN orders ON customers.id = orders.customer_id
WHERE orders.date >= '2025-03-01' AND orders.date <= '2025-03-31'
GROUP BY customers.id
HAVING total_spent > 1000;`}
                  className="text-green-400 font-mono text-sm"
                  speed={5}
                  startDelay={3000}
                  startOnView={isVisible['demo-section']}
                />
              </motion.div>
              
              <motion.div 
                className="flex items-start gap-3"
                initial={{ opacity: 0 }}
                animate={isVisible['demo-section'] ? { opacity: 1 } : {}}
                transition={{ duration: 0.5, delay: 4 }}
              >
                <div className="mt-1">
                  <Database size={16} className="text-indigo-400" />
                </div>
                <div>
                  <div className="text-gray-500 text-xs mb-1">SpeakQL:</div>
                  <div className="text-green-400">
                    <span className="font-medium">24 customers found</span> who spent over $1000 in March 2025.
                    <motion.span 
                      className="block mt-2 text-sm text-gray-300"
                      initial={{ opacity: 0 }}
                      animate={isVisible['demo-section'] ? { opacity: 1 } : {}}
                      transition={{ duration: 0.5, delay: 4.5 }}
                    >
                      Would you like to see their details or analyze their purchasing patterns?
                    </motion.span>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* New Paradigm Section - Enhanced with 3D */}
        <div id="paradigm-section" className="py-16 bg-gradient-to-r from-indigo-900/30 to-purple-900/30 observe-me">
          <div className="max-w-4xl mx-auto px-4 text-center relative">
            <motion.h2 
              className="text-3xl font-bold mb-8 text-gray-100"
              initial={{ opacity: 0, y: 30 }}
              animate={isVisible['paradigm-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8 }}
            >
              The New Paradigm
            </motion.h2>
            
            <div className="flex flex-col md:flex-row items-center justify-center gap-8 mb-8">
              <motion.div 
                className="bg-gray-800 p-6 rounded-xl border border-gray-700 w-full md:w-1/2 relative overflow-hidden"
                initial={{ x: -50, opacity: 0 }}
                animate={isVisible['paradigm-section'] ? { x: 0, opacity: 1 } : {}}
                transition={{ duration: 0.8, delay: 0.2 }}
                whileHover={{ y: -5 }}
              >
                <div className="absolute -right-10 -bottom-10 w-32 h-32 rounded-full bg-red-900/10 blur-xl" />
                <h3 className="text-red-400 font-bold mb-3">Old Way</h3>
                <p className="text-gray-400 mb-4">Humans learning complex SQL syntax</p>
                <div className="bg-gray-900 p-3 rounded text-sm font-mono text-gray-300 overflow-x-auto">
                  SELECT * FROM table WHERE condition GROUP BY field HAVING count {'>'} 0 ORDER BY field;
                </div>
              </motion.div>
              
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={isVisible['paradigm-section'] ? { scale: 1, opacity: 1 } : {}}
                transition={{ duration: 0.5, delay: 0.7 }}
                className="text-indigo-400"
              >
                <ArrowRight className="transform rotate-90 md:rotate-0" size={32} />
              </motion.div>
              
              <motion.div 
                className="bg-gray-800 p-6 rounded-xl border border-indigo-700 w-full md:w-1/2 shadow-lg shadow-indigo-900/20 relative overflow-hidden"
                initial={{ x: 50, opacity: 0 }}
                animate={isVisible['paradigm-section'] ? { x: 0, opacity: 1 } : {}}
                transition={{ duration: 0.8, delay: 0.4 }}
                whileHover={{ y: -5 }}
              >
                <div className="absolute -right-10 -bottom-10 w-32 h-32 rounded-full bg-green-900/10 blur-xl" />
                <h3 className="text-green-400 font-bold mb-3">SpeakQL Way</h3>
                <p className="text-gray-300 mb-4">Databases understanding human language</p>
                <div className="bg-gray-900 p-3 rounded text-sm font-medium text-white">
                  "Show me all sales from last month grouped by product category"
                </div>
              </motion.div>
            </div>
            
            <motion.p 
              className="text-gray-300 max-w-2xl mx-auto"
              initial={{ opacity: 0, y: 20 }}
              animate={isVisible['paradigm-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.8 }}
            >
              SpeakQL bridges the gap between humans and databases, making data accessible to everyone in your organization without SQL expertise.
            </motion.p>
          </div>
        </div>

        {/* Features Section - Enhanced with animations */}
        <div id="features-section" className="max-w-6xl mx-auto py-20 px-4 observe-me">
          <motion.h2 
            className="text-3xl font-bold text-center mb-14 text-gray-100"
            initial={{ opacity: 0, y: 30 }}
            animate={isVisible['features-section'] ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8 }}
          >
            Why Choose SpeakQL
          </motion.h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Brain className="w-8 h-8" />}
              title="AI-Powered Understanding"
              description="Our advanced NLP engine understands context, intent, and business terminology"
              delay={0.2}
              isVisible={isVisible['features-section']}
            />
            <FeatureCard 
              icon={<Database className="w-8 h-8" />}
              title="Universal Database Compatibility"
              description="Works with MySQL, PostgreSQL, SQL Server, MongoDB and more"
              delay={0.4}
              isVisible={isVisible['features-section']}
            />
            <FeatureCard 
              icon={<Zap className="w-8 h-8" />}
              title="Instant Results"
              description="Get answers in milliseconds without writing a single line of SQL"
              delay={0.6}
              isVisible={isVisible['features-section']}
            />
            <FeatureCard 
              icon={<Shield className="w-8 h-8" />}
              title="Enterprise-Grade Security"
              description="Your data stays secure with end-to-end encryption and role-based access"
              delay={0.4}
              isVisible={isVisible['features-section']}
            />
            <FeatureCard 
              icon={<Code className="w-8 h-8" />}
              title="Query Optimization"
              description="Automatically generates efficient SQL for better performance"
              delay={0.6}
              isVisible={isVisible['features-section']}
            />
            <FeatureCard 
              icon={<MessageSquare className="w-8 h-8" />}
              title="Conversational Interface"
              description="Refine queries through natural dialogue and follow-up questions"
              delay={0.8}
              isVisible={isVisible['features-section']}
            />
          </div>
        </div>

        {/* How It Works Section - Enhanced workflow with 3D */}
        <div id="workflow-section" className="bg-gray-800 py-20 observe-me">
          <div className="max-w-6xl mx-auto px-4">
            <motion.h2 
              className="text-3xl font-bold text-center mb-16 text-gray-100"
              initial={{ opacity: 0, y: 30 }}
              animate={isVisible['workflow-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8 }}
            >
              How SpeakQL Works
            </motion.h2>
            
            <div className="grid md:grid-cols-3 gap-12 relative">
              {/* Connecting line */}
              <div className="absolute top-10 left-1/2 transform -translate-x-1/2 hidden md:block z-0">
                <motion.div 
                  className="h-0.5 bg-indigo-700/50 w-4/5 mx-auto"
                  initial={{ width: 0 }}
                  animate={isVisible['workflow-section'] ? { width: '80%' } : {}}
                  transition={{ duration: 1, delay: 1 }}
                />
              </div>
              
              <WorkflowStep 
                number="01"
                title="Connect Your Database"
                description="Securely link SpeakQL to your database with just a few clicks. No schema modifications required."
                delay={0.2}
                isVisible={isVisible['workflow-section']}
              />
              <WorkflowStep 
                number="02"
                title="Ask in Plain Language"
                description="Type or speak your query naturally - as if you're talking to a data analyst colleague."
                delay={0.6}
                isVisible={isVisible['workflow-section']}
              />
              <WorkflowStep 
                number="03"
                title="Get Intelligent Results"
                description="SpeakQL understands your intent, translates to optimized SQL, and delivers results instantly."
                delay={1}
                isVisible={isVisible['workflow-section']}
              />
            </div>
          </div>
        </div>

        {/* Stats Section - New section */}
        <div id="stats-section" className="py-20 bg-gray-900 observe-me">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <StatCounter 
                label="Users" 
                value={10000} 
                suffix="+" 
                icon={<Users />} 
                delay={0.2}
                isVisible={isVisible['stats-section']}
              />
              <StatCounter 
                label="Databases Supported" 
                value={12} 
                icon={<Database />} 
                delay={0.4}
                isVisible={isVisible['stats-section']}
              />
              <StatCounter 
                label="Queries Per Day" 
                value={5} 
                suffix="M+" 
                icon={<MessageSquare />} 
                delay={0.6}
                isVisible={isVisible['stats-section']}
              />
              <StatCounter 
                label="Accuracy Rate" 
                value={99.7} 
                suffix="%" 
                icon={<CheckCircle />}
                delay={0.8} 
                isVisible={isVisible['stats-section']}
              />
            </div>
          </div>
        </div>

        {/* Testimonials Section - Enhanced with animations */}
        <div id="testimonials-section" className="py-20 bg-gradient-to-b from-gray-900 to-gray-800 observe-me">
          <div className="max-w-6xl mx-auto px-4">
            <motion.h2 
              className="text-3xl font-bold text-center mb-16 text-gray-100"
              initial={{ opacity: 0, y: 30 }}
              animate={isVisible['testimonials-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8 }}
            >
              What Our Users Say
            </motion.h2>
            
            <div className="grid md:grid-cols-2 gap-8">
              <TestimonialCard
                quote="SpeakQL has transformed how our non-technical team accesses data. They can now get insights without waiting for the data team."
                author="Sarah Chen"
                role="CTO, DataFirst Inc."
                rating={5}
                delay={0.3}
                isVisible={isVisible['testimonials-section']}
              />
              <TestimonialCard
                quote="The natural language interface is revolutionary. Our analysts spend more time analyzing data and less time writing SQL queries."
                author="Michael Rodriguez"
                role="Data Science Lead, TechGrowth"
                rating={5}
                delay={0.5}
                isVisible={isVisible['testimonials-section']}
              />
            </div>
          </div>
        </div>

        {/* CTA Section - Enhanced with animations */}
        <div id="cta-section" className="bg-gradient-to-r from-indigo-900 to-purple-900 py-16 observe-me">
          <div className="max-w-4xl mx-auto text-center px-4">
            <motion.h2 
              className="text-3xl font-bold text-white mb-4"
              initial={{ opacity: 0, y: 30 }}
              animate={isVisible['cta-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8 }}
            >
              Ready to let your database understand humans?
            </motion.h2>
            
            <motion.p 
              className="text-indigo-200 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={isVisible['cta-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              Join thousands of companies democratizing data access with natural language.
            </motion.p>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isVisible['cta-section'] ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.4 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
            >
              <Button
                onClick={() => navigate('/signup')}
                className="bg-white hover:bg-gray-100 text-indigo-900 px-8 py-6 rounded-lg text-lg font-medium shadow-xl transition-all"
              >
                <span className="flex items-center">
                  Start Your Free Trial
                  <motion.div
                    animate={{ x: [0, 5, 0] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  >
                    <ChevronRight className="ml-1" />
                  </motion.div>
                </span>
              </Button>
            </motion.div>
            
            <motion.p 
              className="text-indigo-300 mt-4 text-sm"
              initial={{ opacity: 0 }}
              animate={isVisible['cta-section'] ? { opacity: 1 } : {}}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              No credit card required • 14-day free trial
            </motion.p>
          </div>
        </div>

        {/* Footer - Enhanced with animations */}
        <footer className="bg-black py-12">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                <motion.div 
                  className="flex items-center gap-2 mb-4"
                  whileHover={{ x: 5 }}
                  transition={{ type: "spring", stiffness: 400 }}
                >
                  <Database className="text-indigo-400 w-6 h-6" />
                  <span className="text-xl font-bold text-indigo-300">SpeakQL</span>
                </motion.div>
                <p className="text-gray-500 text-sm">
                  Teaching databases to understand humans, not humans to speak SQL.
                </p>
              </motion.div>
              
              <FooterColumn 
                title="Product" 
                links={[
                  { label: "Features", href: "#" },
                  { label: "Pricing", href: "#" },
                  { label: "Enterprise", href: "#" }
                ]}
                delay={0.2}
              />
              
              <FooterColumn 
                title="Resources" 
                links={[
                  { label: "Documentation", href: "#" },
                  { label: "API Reference", href: "#" },
                  { label: "Blog", href: "#" }
                ]}
                delay={0.3}
              />
              
              <FooterColumn 
                title="Company" 
                links={[
                  { label: "About", href: "#" },
                  { label: "Careers", href: "#" },
                  { label: "Contact", href: "#" }
                ]}
                delay={0.4}
              />
            </div>
            
            <motion.div 
              className="pt-8 border-t border-gray-800 flex flex-col md:flex-row justify-between items-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.8 }}
            >
              <span className="text-gray-600 text-sm">&copy; {new Date().getFullYear()} SpeakQL. All rights reserved.</span>
              <div className="flex gap-4 mt-4 md:mt-0">
                <Medal className="text-yellow-400 w-5 h-5" />
                <Star className="text-yellow-400 w-5 h-5" />
              </div>
            </motion.div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default HomePage;

