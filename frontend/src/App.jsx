import React, { useState } from 'react';
import CalculationBuilder from './components/CalculationBuilder';
import ReportBuilder from './components/ReportBuilder';
import { Calculator, BarChart3 } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('reports');

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('reports')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'reports'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              Report Builder
            </button>
            <button
              onClick={() => setActiveTab('calculations')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'calculations'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Calculator className="h-4 w-4" />
              Calculation Builder
            </button>
          </div>
        </div>
      </nav>

      {activeTab === 'reports' && <ReportBuilder />}
      {activeTab === 'calculations' && <CalculationBuilder />}
    </div>
  );
}

export default App;