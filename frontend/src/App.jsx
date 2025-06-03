// frontend/src/App.jsx
import React, { useState } from 'react';
import CalculationBuilder from './components/CalculationBuilder';
import ReportTemplateBuilder from './components/ReportTemplateBuilder';
import { NotificationProvider } from './components/NotificationSystem';

function App() {
  const [activeTab, setActiveTab] = useState('calculations');

  return (
    <NotificationProvider>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
                <span className="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  v3.0
                </span>
              </div>
              
              <nav className="flex space-x-8">
                <button
                  onClick={() => setActiveTab('calculations')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'calculations'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Calculations
                </button>
                <button
                  onClick={() => setActiveTab('templates')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'templates'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Report Templates
                </button>
              </nav>
            </div>
          </div>
        </div>

        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          {activeTab === 'calculations' && <CalculationBuilder />}
          {activeTab === 'templates' && <ReportTemplateBuilder />}
        </main>

        <footer className="bg-white border-t mt-12">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center text-sm text-gray-500">
              <p>© 2025 Report Builder v3. Advanced SQL report generation system.</p>
              <div className="flex space-x-4">
                <span>FastAPI Backend</span>
                <span>•</span>
                <span>React Frontend</span>
                <span>•</span>
                <span>SQLite Database</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </NotificationProvider>
  );
}

export default App;