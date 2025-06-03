// frontend/src/components/CalculationBuilder.jsx
import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, Edit3, Calculator, Database } from 'lucide-react';

const CalculationBuilder = () => {
  const [calculations, setCalculations] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editingCalculation, setEditingCalculation] = useState(null);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    aggregation_function: 'SUM',
    source_model: 'TrancheBal',
    source_field: '',
    group_level: 'deal',
    weight_field: ''
  });

  // Available options for the ORM-based system
  const aggregationFunctions = [
    { value: 'SUM', label: 'SUM - Total amount', description: 'Add all values together' },
    { value: 'AVG', label: 'AVG - Average', description: 'Calculate average value' },
    { value: 'COUNT', label: 'COUNT - Count', description: 'Count number of records' },
    { value: 'MIN', label: 'MIN - Minimum', description: 'Find smallest value' },
    { value: 'MAX', label: 'MAX - Maximum', description: 'Find largest value' },
    { value: 'WEIGHTED_AVG', label: 'WEIGHTED_AVG - Weighted Average', description: 'Balance-weighted average' }
  ];

  const sourceModels = [
    { value: 'Deal', label: 'Deal', description: 'Deal-level information' },
    { value: 'Tranche', label: 'Tranche', description: 'Tranche-level information' },
    { value: 'TrancheBal', label: 'TrancheBal', description: 'Financial data and balances' }
  ];

  const groupLevels = [
    { value: 'deal', label: 'Deal Level', description: 'Aggregated at deal level' },
    { value: 'tranche', label: 'Tranche Level', description: 'Aggregated at tranche level' }
  ];

  // Available fields by source model
  const availableFields = {
    Deal: [
      { value: 'dl_nbr', label: 'Deal Number', type: 'number' },
      { value: 'issr_cde', label: 'Issuer Code', type: 'text' },
      { value: 'cdi_file_nme', label: 'CDI File Name', type: 'text' }
    ],
    Tranche: [
      { value: 'tr_id', label: 'Tranche ID', type: 'text' },
      { value: 'tr_cusip_id', label: 'CUSIP ID', type: 'text' }
    ],
    TrancheBal: [
      { value: 'tr_end_bal_amt', label: 'Ending Balance Amount', type: 'currency' },
      { value: 'tr_prin_rel_ls_amt', label: 'Principal Release Loss Amount', type: 'currency' },
      { value: 'tr_pass_thru_rte', label: 'Pass Through Rate', type: 'percentage' },
      { value: 'tr_accrl_days', label: 'Accrual Days', type: 'number' },
      { value: 'tr_int_dstrb_amt', label: 'Interest Distribution Amount', type: 'currency' },
      { value: 'tr_prin_dstrb_amt', label: 'Principal Distribution Amount', type: 'currency' },
      { value: 'tr_int_accrl_amt', label: 'Interest Accrual Amount', type: 'currency' },
      { value: 'tr_int_shtfl_amt', label: 'Interest Shortfall Amount', type: 'currency' },
      { value: 'cycle_cde', label: 'Cycle Code', type: 'number' }
    ]
  };

  useEffect(() => {
    fetchCalculations();
  }, []);

  const fetchCalculations = async () => {
    try {
      const response = await fetch('/api/calculations');
      if (response.ok) {
        const data = await response.json();
        setCalculations(data);
      } else {
        setError('Failed to fetch calculations');
      }
    } catch (error) {
      console.error('Error fetching calculations:', error);
      setError('Error fetching calculations');
    }
  };

  const handleSubmit = async () => {
    setError(null);
    
    // Validation
    if (!formData.name || !formData.source_field) {
      setError('Please fill in all required fields');
      return;
    }

    if (formData.aggregation_function === 'WEIGHTED_AVG' && !formData.weight_field) {
      setError('Weighted average calculations require a weight field');
      return;
    }

    try {
      const url = editingCalculation 
        ? `/api/calculations/${editingCalculation.id}`
        : '/api/calculations';
      
      const method = editingCalculation ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await fetchCalculations();
        handleCancel();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error saving calculation');
      }
    } catch (error) {
      console.error('Error saving calculation:', error);
      setError('Error saving calculation');
    }
  };

  const handleDelete = async (calcId) => {
    if (!confirm('Are you sure you want to delete this calculation? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/calculations/${calcId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchCalculations();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error deleting calculation');
      }
    } catch (error) {
      console.error('Error deleting calculation:', error);
      setError('Error deleting calculation');
    }
  };

  const handleEdit = (calculation) => {
    setEditingCalculation(calculation);
    setFormData({
      name: calculation.name,
      description: calculation.description || '',
      aggregation_function: calculation.aggregation_function,
      source_model: calculation.source_model,
      source_field: calculation.source_field,
      group_level: calculation.group_level,
      weight_field: calculation.weight_field || ''
    });
    setIsEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditingCalculation(null);
    setError(null);
    setFormData({
      name: '',
      description: '',
      aggregation_function: 'SUM',
      source_model: 'TrancheBal',
      source_field: '',
      group_level: 'deal',
      weight_field: ''
    });
  };

  const getPreviewFormula = () => {
    if (!formData.aggregation_function || !formData.source_field) {
      return 'Select aggregation function and field to see preview';
    }

    const field = `${formData.source_model}.${formData.source_field}`;
    
    if (formData.aggregation_function === 'WEIGHTED_AVG') {
      const weightField = formData.weight_field ? `${formData.source_model}.${formData.weight_field}` : 'weight_field';
      return `SUM(${field} * ${weightField}) / NULLIF(SUM(${weightField}), 0)`;
    } else {
      return `${formData.aggregation_function}(${field})`;
    }
  };

  const getFieldTypeIcon = (type) => {
    switch(type) {
      case 'currency': return '💰';
      case 'percentage': return '📊';
      case 'number': return '🔢';
      case 'text': return '📝';
      default: return '📄';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Calculator className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">ORM Calculation Builder</h1>
          </div>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
              New Calculation
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {isEditing && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6 border-2 border-blue-200">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">
              {editingCalculation ? 'Edit Calculation' : 'Create New Calculation'}
            </h2>
            
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Calculation Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Total Ending Balance"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Group Level *
                  </label>
                  <select
                    value={formData.group_level}
                    onChange={(e) => setFormData({ ...formData, group_level: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {groupLevels.map(level => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {groupLevels.find(l => l.value === formData.group_level)?.description}
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of this calculation"
                />
              </div>

              {/* Source Configuration */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source Model *
                  </label>
                  <select
                    value={formData.source_model}
                    onChange={(e) => setFormData({ ...formData, source_model: e.target.value, source_field: '' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {sourceModels.map(model => (
                      <option key={model.value} value={model.value}>
                        {model.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {sourceModels.find(m => m.value === formData.source_model)?.description}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Aggregation Function *
                  </label>
                  <select
                    value={formData.aggregation_function}
                    onChange={(e) => setFormData({ ...formData, aggregation_function: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {aggregationFunctions.map(func => (
                      <option key={func.value} value={func.value}>
                        {func.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {aggregationFunctions.find(f => f.value === formData.aggregation_function)?.description}
                  </p>
                </div>
              </div>

              {/* Field Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Source Field *
                </label>
                <select
                  value={formData.source_field}
                  onChange={(e) => setFormData({ ...formData, source_field: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a field...</option>
                  {availableFields[formData.source_model]?.map(field => (
                    <option key={field.value} value={field.value}>
                      {getFieldTypeIcon(field.type)} {field.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Weight Field for Weighted Average */}
              {formData.aggregation_function === 'WEIGHTED_AVG' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Weight Field * (for weighted average)
                  </label>
                  <select
                    value={formData.weight_field}
                    onChange={(e) => setFormData({ ...formData, weight_field: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select weight field...</option>
                    {availableFields[formData.source_model]?.map(field => (
                      <option key={field.value} value={field.value}>
                        {getFieldTypeIcon(field.type)} {field.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Field to use as weight for the weighted average calculation
                  </p>
                </div>
              )}

              {/* ORM Formula Preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Generated ORM Formula Preview
                </label>
                <div className="bg-gray-100 rounded p-3 border">
                  <code className="text-sm text-gray-800 font-mono">{getPreviewFormula()}</code>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  <strong>Model:</strong> {formData.source_model} | 
                  <strong> Function:</strong> {formData.aggregation_function} | 
                  <strong> Level:</strong> {formData.group_level}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleSubmit}
                  className="flex items-center gap-2 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Save className="h-4 w-4" />
                  {editingCalculation ? 'Update Calculation' : 'Save Calculation'}
                </button>
                <button
                  onClick={handleCancel}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Available Calculations List */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Available Calculations</h2>
          <div className="grid gap-4">
            {calculations.map((calc) => (
              <div key={calc.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">{calc.name}</h3>
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                        {calc.aggregation_function}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        calc.group_level === 'deal' ? 'bg-green-100 text-green-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {calc.group_level === 'deal' ? 'Deal Level' : 'Tranche Level'}
                      </span>
                      <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                        {calc.source_model}
                      </span>
                    </div>
                    {calc.description && (
                      <p className="text-gray-600 mb-2">{calc.description}</p>
                    )}
                    
                    <div className="bg-gray-50 rounded p-3 mb-2">
                      <div className="text-sm text-gray-700">
                        <strong>Source:</strong> {calc.source_model}.{calc.source_field}
                        {calc.weight_field && (
                          <span> | <strong>Weight:</strong> {calc.source_model}.{calc.weight_field}</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Database className="h-3 w-3" />
                      <span>ORM-based calculation using SQLAlchemy func.{calc.aggregation_function.toLowerCase()}</span>
                    </div>
                    
                    {calc.created_at && (
                      <div className="text-xs text-gray-400 mt-2">
                        Created: {new Date(calc.created_at).toLocaleString()}
                        {calc.updated_at && calc.updated_at !== calc.created_at && (
                          <span className="ml-4">Updated: {new Date(calc.updated_at).toLocaleString()}</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleEdit(calc)}
                      className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                      title="Edit calculation"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(calc.id)}
                      className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete calculation"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {calculations.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Calculator className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No calculations found. Create your first calculation to get started.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CalculationBuilder;