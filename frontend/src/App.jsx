// frontend/src/App.jsx
import React, { useState } from 'react';
import CalculationBuilder from './components/CalculationBuilder';
import ReportTemplateBuilder from './components/ReportTemplateBuilder';
import { Calculator, FileText, Database } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('templates');

  const tabs = [
    {
      id: 'templates',
      label: 'Report Templates',
      icon: FileText,
      component: ReportTemplateBuilder,
      description: 'Create and manage reusable report templates'
    },
    {
      id: 'calculations',
      label: 'Calculations',
      icon: Calculator,
      component: CalculationBuilder,
      description: 'Define ORM-based calculations using SQLAlchemy'
    }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 py-4">
              <div className="flex items-center gap-2">
                <Database className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Reporting System</h1>
                  <p className="text-sm text-gray-500">ORM-based Financial Reports</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                      activeTab === tab.id
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                    title={tab.description}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* Feature Banner */}
      <div className="bg-blue-50 border-b border-blue-200">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-blue-700">
              <span className="text-sm font-medium">🎉 New Features:</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-blue-600">
              <span>✓ Template-based Reports</span>
              <span>✓ ORM Calculations</span>
              <span>✓ LEFT JOIN Preservation</span>
              <span>✓ SQLAlchemy Integration</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        {ActiveComponent && <ActiveComponent />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              <p>Refactored Reporting System v2.0</p>
              <p className="mt-1">Now using ORM queries and template-based architecture</p>
            </div>
            <div className="text-sm text-gray-400">
              <div className="flex items-center gap-4">
                <span>API Docs: <a href="/docs" className="text-blue-600 hover:underline">/docs</a></span>
                <span>Health: <a href="/health" className="text-blue-600 hover:underline">/health</a></span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;