import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, Edit3, Calculator, Info } from 'lucide-react';

const CalculationBuilder = () => {
  const [calculations, setCalculations] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editingCalculation, setEditingCalculation] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    aggregation_method: 'SUM',
    source_field: '',
    filter_conditions: [],
    dependencies: []
  });

  // Available aggregation methods
  const aggregationMethods = [
    { value: 'SUM', label: 'SUM - Total amount', description: 'Add all values together' },
    { value: 'AVG', label: 'AVG - Average', description: 'Calculate average value' },
    { value: 'COUNT', label: 'COUNT - Count', description: 'Count number of records' },
    { value: 'MIN', label: 'MIN - Minimum', description: 'Find smallest value' },
    { value: 'MAX', label: 'MAX - Maximum', description: 'Find largest value' },
    { value: 'WEIGHTED_AVG', label: 'WEIGHTED_AVG - Weighted Average', description: 'Balance-weighted average' }
  ];

  // Available fields grouped by table
  const availableFields = {
    'Deal Information': [
      { value: 'd.dl_nbr', label: 'Deal Number', table: 'deal', type: 'number' },
      { value: 'd.issr_cde', label: 'Issuer Code', table: 'deal', type: 'text' },
      { value: 'd.cdi_file_nme', label: 'CDI File Name', table: 'deal', type: 'text' }
    ],
    'Tranche Information': [
      { value: 't.tr_id', label: 'Tranche ID', table: 'tranche', type: 'text' },
      { value: 't.tr_cusip_id', label: 'CUSIP ID', table: 'tranche', type: 'text' }
    ],
    'Financial Data': [
      { value: 'tb.tr_end_bal_amt', label: 'Ending Balance Amount', table: 'tranchebal', type: 'currency' },
      { value: 'tb.tr_prin_rel_ls_amt', label: 'Principal Release Loss Amount', table: 'tranchebal', type: 'currency' },
      { value: 'tb.tr_pass_thru_rte', label: 'Pass Through Rate', table: 'tranchebal', type: 'percentage' },
      { value: 'tb.tr_accrl_days', label: 'Accrual Days', table: 'tranchebal', type: 'number' },
      { value: 'tb.tr_int_dstrb_amt', label: 'Interest Distribution Amount', table: 'tranchebal', type: 'currency' },
      { value: 'tb.tr_prin_dstrb_amt', label: 'Principal Distribution Amount', table: 'tranchebal', type: 'currency' },
      { value: 'tb.tr_int_accrl_amt', label: 'Interest Accrual Amount', table: 'tranchebal', type: 'currency' },
      { value: 'tb.tr_int_shtfl_amt', label: 'Interest Shortfall Amount', table: 'tranchebal', type: 'currency' },
      { value: 'tb.cycle_cde', label: 'Cycle Code', table: 'tranchebal', type: 'number' }
    ]
  };

  // Get all fields flattened
  const allFields = Object.values(availableFields).flat();

  useEffect(() => {
    fetchCalculations();
  }, []);

  const fetchCalculations = async () => {
    try {
      const response = await fetch('/api/reports/calculations');
      const data = await response.json();
      setCalculations(data);
    } catch (error) {
      console.error('Error fetching calculations:', error);
    }
  };

  const generateFormula = () => {
    if (!formData.aggregation_method || !formData.source_field) {
      return '';
    }

    const selectedField = allFields.find(f => f.value === formData.source_field);
    
    if (formData.aggregation_method === 'WEIGHTED_AVG' && selectedField?.type === 'percentage') {
      // Special case for weighted average rate
      return `SUM(tb.tr_end_bal_amt * ${formData.source_field}) / NULLIF(SUM(tb.tr_end_bal_amt), 0)`;
    } else if (formData.aggregation_method === 'COUNT') {
      if (selectedField?.table === 'tranche') {
        return `COUNT(DISTINCT ${formData.source_field})`;
      } else {
        return `COUNT(${formData.source_field})`;
      }
    } else {
      return `${formData.aggregation_method}(${formData.source_field})`;
    }
  };

  const generateSourceTables = () => {
    if (!formData.source_field) return [];
    
    const selectedField = allFields.find(f => f.value === formData.source_field);
    const tables = [];
    
    // Always need deal table
    if (!tables.includes('deal d')) tables.push('deal d');
    
    // Add tranche table if needed
    if (selectedField?.table === 'tranche' || selectedField?.table === 'tranchebal') {
      if (!tables.includes('tranche t')) tables.push('tranche t');
    }
    
    // Add tranchebal table if needed
    if (selectedField?.table === 'tranchebal') {
      if (!tables.includes('tranchebal tb')) tables.push('tranchebal tb');
    }
    
    return tables;
  };

  const handleSubmit = async () => {
    const formula = generateFormula();
    const sourceTables = generateSourceTables();
    
    if (!formula) {
      alert('Please select both aggregation method and source field');
      return;
    }

    try {
      const url = editingCalculation 
        ? `/api/reports/calculations/${editingCalculation.name}`
        : '/api/reports/calculations';
      
      const method = editingCalculation ? 'PUT' : 'POST';
      
      const requestData = {
        name: formData.name,
        description: formData.description,
        formula: formula,
        aggregation_method: formData.aggregation_method,
        source_tables: sourceTables,
        dependencies: formData.dependencies.filter(dep => dep.trim() !== '')
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        await fetchCalculations();
        handleCancel();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error saving calculation:', error);
      alert('Error saving calculation');
    }
  };

  const handleDelete = async (calcName) => {
    if (!confirm(`Are you sure you want to delete the calculation "${calcName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/reports/calculations/${calcName}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchCalculations();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting calculation:', error);
      alert('Error deleting calculation');
    }
  };

  const handleEdit = (calculation) => {
    setEditingCalculation(calculation);
    
    // Try to reverse-engineer the field selection from the formula
    const sourceField = allFields.find(field => 
      calculation.formula.includes(field.value)
    )?.value || '';

    setFormData({
      name: calculation.name,
      description: calculation.description || '',
      aggregation_method: calculation.aggregation_method,
      source_field: sourceField,
      filter_conditions: [],
      dependencies: calculation.dependencies || []
    });
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditingCalculation(null);
    setFormData({
      name: '',
      description: '',
      aggregation_method: 'SUM',
      source_field: '',
      filter_conditions: [],
      dependencies: []
    });
  };

  const handleDependencyChange = (index, value) => {
    const newDeps = [...formData.dependencies];
    newDeps[index] = value;
    setFormData({ ...formData, dependencies: newDeps });
  };

  const addDependency = () => {
    setFormData({
      ...formData,
      dependencies: [...formData.dependencies, '']
    });
  };

  const removeDependency = (index) => {
    const newDeps = formData.dependencies.filter((_, i) => i !== index);
    setFormData({ ...formData, dependencies: newDeps });
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
            <h1 className="text-3xl font-bold text-gray-900">Calculation Builder</h1>
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="e.g., total_ending_balance"
                    disabled={editingCalculation !== null}
                  />
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
              </div>

              {/* Aggregation Method */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Aggregation Method *
                </label>
                <select
                  value={formData.aggregation_method}
                  onChange={(e) => setFormData({ ...formData, aggregation_method: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {aggregationMethods.map(method => (
                    <option key={method.value} value={method.value} title={method.description}>
                      {method.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {aggregationMethods.find(m => m.value === formData.aggregation_method)?.description}
                </p>
              </div>

              {/* Source Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Field to Calculate *
                </label>
                <select
                  value={formData.source_field}
                  onChange={(e) => setFormData({ ...formData, source_field: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a field to calculate...</option>
                  {Object.entries(availableFields).map(([category, fields]) => (
                    <optgroup key={category} label={category}>
                      {fields.map(field => (
                        <option key={field.value} value={field.value}>
                          {getFieldTypeIcon(field.type)} {field.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>

              {/* Generated Formula Preview */}
              {formData.aggregation_method && formData.source_field && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Generated SQL Formula
                  </label>
                  <div className="bg-gray-100 rounded p-3 border">
                    <code className="text-sm text-gray-800 font-mono">{generateFormula()}</code>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    <strong>Required Tables:</strong> {generateSourceTables().join(', ')}
                  </div>
                </div>
              )}

              {/* Dependencies */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dependencies (Other Calculations)
                </label>
                <div className="space-y-2">
                  {formData.dependencies.map((dep, index) => (
                    <div key={index} className="flex gap-2">
                      <select
                        value={dep}
                        onChange={(e) => handleDependencyChange(index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select a calculation...</option>
                        {calculations.map(calc => (
                          <option key={calc.name} value={calc.name}>{calc.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => removeDependency(index)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addDependency}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    + Add Dependency
                  </button>
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
              <div key={calc.name} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">{calc.name}</h3>
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">{calc.aggregation_method}</span>
                    </div>
                    {calc.description && (
                      <p className="text-gray-600 mb-2">{calc.description}</p>
                    )}
                    <div className="bg-gray-50 rounded p-3 mb-2">
                      <code className="text-sm text-gray-800">{calc.formula}</code>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-500 mb-2">
                      <span>Tables: {calc.source_tables.join(', ')}</span>
                      {calc.dependencies.length > 0 && (
                        <span>Dependencies: {calc.dependencies.join(', ')}</span>
                      )}
                    </div>
                    {(calc.created_at || calc.updated_at) && (
                      <div className="text-xs text-gray-400">
                        {calc.created_at && <span>Created: {new Date(calc.created_at).toLocaleString()}</span>}
                        {calc.updated_at && <span className="ml-4">Updated: {new Date(calc.updated_at).toLocaleString()}</span>}
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
                      onClick={() => handleDelete(calc.name)}
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
        </div>
      </div>
    </div>
  );
};

export default CalculationBuilder;