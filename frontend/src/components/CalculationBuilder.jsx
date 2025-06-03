import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, Edit3, Calculator, Eye, EyeOff, Code, Copy, Check } from 'lucide-react';

const CalculationBuilder = () => {
  const [calculations, setCalculations] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editingCalculation, setEditingCalculation] = useState(null);
  const [showSqlPreview, setShowSqlPreview] = useState(false);
  const [sqlPreviewData, setSqlPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [expandedCalculations, setExpandedCalculations] = useState(new Set());
  const [existingSqlPreviews, setExistingSqlPreviews] = useState({});
  const [copiedSql, setCopiedSql] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    aggregation_method: 'SUM',
    group_level: 'deal',
    source_field: '',
    filter_conditions: [],
    dependencies: []
  });

  // Available group levels
  const groupLevels = [
    { value: 'deal', label: 'Deal Level Only', description: 'Only appears in deal-level reports' },
    { value: 'tranche', label: 'Tranche Level Only', description: 'Only appears in tranche-level reports' }
  ];
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
    console.log('CalculationBuilder mounted, calculations state:', calculations);
    fetchCalculations();
  }, []);

  // Debug effect to monitor calculations state changes
  useEffect(() => {
    console.log('Calculations state changed:', calculations, 'Type:', typeof calculations, 'Is Array:', Array.isArray(calculations));
  }, [calculations]);

  // Regenerate SQL preview when form fields change
  useEffect(() => {
    if (showSqlPreview && formData.aggregation_method && formData.source_field) {
      generateSqlPreview();
    }
  }, [formData.aggregation_method, formData.source_field, formData.group_level]);

  const fetchCalculations = async () => {
    try {
      const response = await fetch('/api/calculations');
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

  const generateSqlPreview = async () => {
    if (!formData.aggregation_method || !formData.source_field) {
      setSqlPreviewData(null);
      return;
    }

    setLoadingPreview(true);
    try {
      const formula = generateFormula();
      const sourceTables = generateSourceTables();
      
      const calculationData = {
        name: formData.name || 'preview_calculation',
        formula: formula,
        aggregation_method: formData.aggregation_method,
        group_level: formData.group_level,
        source_tables: sourceTables
      };

      const response = await fetch('/api/calculations/preview-sql', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(calculationData),
      });

      if (response.ok) {
        const previewData = await response.json();
        setSqlPreviewData(previewData);
      } else {
        console.error('Failed to generate SQL preview');
        setSqlPreviewData(null);
      }
    } catch (error) {
      console.error('Error generating SQL preview:', error);
      setSqlPreviewData(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const fetchExistingCalculationSql = async (calcName, groupLevel) => {
    try {
      setLoadingPreview(true);
      
      // Fetch for both deal and tranche levels if group_level is 'both'
      const levels = groupLevel === 'both' ? ['deal', 'tranche'] : [groupLevel];
      const sqlData = {};
      
      for (const level of levels) {
        const response = await fetch(`/api/calculations/${calcName}/preview-sql?aggregation_level=${level}`);
        if (response.ok) {
          const data = await response.json();
          sqlData[level] = data;
        }
      }
      
      setExistingSqlPreviews(prev => ({
        ...prev,
        [calcName]: sqlData
      }));
      
    } catch (error) {
      console.error('Error fetching SQL preview:', error);
    } finally {
      setLoadingPreview(false);
    }
  };

  const toggleCalculationExpansion = async (calcName, calc) => {
    setExpandedCalculations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(calcName)) {
        newSet.delete(calcName);
      } else {
        newSet.add(calcName);
        // Fetch SQL preview when expanding
        fetchExistingCalculationSql(calcName, calc.group_level);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (sql, calcName = 'preview') => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopiedSql(calcName);
      setTimeout(() => setCopiedSql(null), 2000);
    } catch (err) {
      console.error('Failed to copy SQL:', err);
    }
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
        ? `/api/calculations/${editingCalculation.name}`
        : '/api/calculations';
      
      const method = editingCalculation ? 'PUT' : 'POST';
      
      const requestData = {
        name: formData.name,
        description: formData.description,
        formula: formula,
        aggregation_method: formData.aggregation_method,
        group_level: formData.group_level,
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
      const response = await fetch(`/api/calculations/${calcName}`, {
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
    setShowSqlPreview(false);
    setSqlPreviewData(null);
    setLoadingPreview(false);
    
    // Try to reverse-engineer the field selection from the formula
    const sourceField = allFields.find(field => 
      calculation.formula.includes(field.value)
    )?.value || '';

    setFormData({
      name: calculation.name,
      description: calculation.description || '',
      aggregation_method: calculation.aggregation_method,
      group_level: calculation.group_level || 'deal',
      source_field: sourceField,
      filter_conditions: [],
      dependencies: calculation.dependencies || []
    });
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditingCalculation(null);
    setShowSqlPreview(false);
    setSqlPreviewData(null);
    setLoadingPreview(false);
    setFormData({
      name: '',
      description: '',
      aggregation_method: 'SUM',
      group_level: 'deal',
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

  // Safety check - ensure calculations is always an array
  const safeCalculations = Array.isArray(calculations) ? calculations : [];
  
  console.log('Render - calculations:', calculations, 'safeCalculations:', safeCalculations);

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

              {/* Group Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Level *
                </label>
                <select
                  value={formData.group_level}
                  onChange={(e) => setFormData({ ...formData, group_level: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Array.isArray(groupLevels) && groupLevels.map(level => (
                    <option key={level.value} value={level.value} title={level.description}>
                      {level.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {groupLevels.find(l => l.value === formData.group_level)?.description}
                </p>
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
                  {Array.isArray(aggregationMethods) && aggregationMethods.map(method => (
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

              {/* SQL Preview Section */}
              {formData.aggregation_method && formData.source_field && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Full SQL Subquery Preview
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        if (showSqlPreview) {
                          setShowSqlPreview(false);
                          setSqlPreviewData(null);
                        } else {
                          setShowSqlPreview(true);
                          generateSqlPreview();
                        }
                      }}
                      className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition-colors disabled:opacity-50"
                      disabled={!formData.aggregation_method || !formData.source_field || loadingPreview}
                    >
                      {loadingPreview ? (
                        <>
                          <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                          Loading...
                        </>
                      ) : showSqlPreview ? (
                        <>
                          <EyeOff className="h-4 w-4" />
                          Hide SQL
                        </>
                      ) : (
                        <>
                          <Eye className="h-4 w-4" />
                          Preview SQL
                        </>
                      )}
                    </button>
                  </div>
                  
                  {showSqlPreview && (
                    <div className="bg-gray-900 rounded-lg p-4 border-2 border-gray-200">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Code className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-400 font-medium">SQL Subquery Preview</span>
                        </div>
                        {sqlPreviewData && (
                          <button
                            onClick={() => copyToClipboard(
                              sqlPreviewData.deal_level_sql || sqlPreviewData.tranche_level_sql || 'No SQL available',
                              'preview'
                            )}
                            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                          >
                            {copiedSql === 'preview' ? (
                              <>
                                <Check className="h-3 w-3" />
                                Copied!
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3" />
                                Copy
                              </>
                            )}
                          </button>
                        )}
                      </div>
                      
                      {loadingPreview ? (
                        <div className="flex items-center justify-center py-8">
                          <div className="animate-spin h-6 w-6 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                          <span className="ml-3 text-gray-400">Generating SQL preview...</span>
                        </div>
                      ) : sqlPreviewData ? (
                        <div className="space-y-4">
                          {sqlPreviewData.deal_level_sql && (
                            <div>
                              <div className="text-xs text-gray-400 mb-2 font-medium">Deal Level SQL:</div>
                              <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
                                {sqlPreviewData.deal_level_sql}
                              </pre>
                            </div>
                          )}
                          
                          {sqlPreviewData.tranche_level_sql && (
                            <div>
                              <div className="text-xs text-gray-400 mb-2 font-medium">Tranche Level SQL:</div>
                              <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
                                {sqlPreviewData.tranche_level_sql}
                              </pre>
                            </div>
                          )}
                          
                          {sqlPreviewData.deal_level_params && Object.keys(sqlPreviewData.deal_level_params).length > 0 && (
                            <div className="mt-3 p-2 bg-blue-900 rounded text-xs text-blue-200">
                              <strong>Sample Parameters:</strong> {JSON.stringify(sqlPreviewData.deal_level_params, null, 2)}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-gray-400 text-sm py-4">
                          Select aggregation method and field to see SQL preview
                        </div>
                      )}
                      
                      <div className="mt-3 p-2 bg-blue-900 rounded text-xs text-blue-200">
                        <strong>💡 Tip:</strong> This subquery will be used in a larger LEFT JOIN when generating reports. 
                        The actual filters (deals, tranches, cycles) will be applied based on user selections in the Report Builder.
                      </div>
                    </div>
                  )}
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
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        calc.group_level === 'deal' ? 'bg-green-100 text-green-800' :
                        calc.group_level === 'tranche' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {calc.group_level === 'both' ? 'Both Levels' : 
                         calc.group_level === 'deal' ? 'Deal Level' : 'Tranche Level'}
                      </span>
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
                      onClick={() => toggleCalculationExpansion(calc.name, calc)}
                      className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-md transition-colors"
                      title="Preview SQL"
                    >
                      {expandedCalculations.has(calc.name) ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
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
                
                {/* SQL Preview for existing calculation */}
                {expandedCalculations.has(calc.name) && (
                  <div className="mt-4 bg-gray-900 rounded-lg p-4 border-2 border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Code className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-400 font-medium">SQL Subquery for "{calc.name}"</span>
                      </div>
                      {existingSqlPreviews[calc.name] && (
                        <button
                          onClick={() => {
                            const sqlData = existingSqlPreviews[calc.name];
                            const sql = sqlData.deal?.sql || sqlData.tranche?.sql || 'No SQL available';
                            copyToClipboard(sql, calc.name);
                          }}
                          className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                        >
                          {copiedSql === calc.name ? (
                            <>
                              <Check className="h-3 w-3" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" />
                              Copy
                            </>
                          )}
                        </button>
                      )}
                    </div>
                    
                    {loadingPreview ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin h-6 w-6 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                        <span className="ml-3 text-gray-400">Loading SQL preview...</span>
                      </div>
                    ) : existingSqlPreviews[calc.name] ? (
                      <div className="space-y-4">
                        {existingSqlPreviews[calc.name].deal && (
                          <div>
                            <div className="text-xs text-gray-400 mb-2 font-medium">Deal Level SQL:</div>
                            <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
                              {existingSqlPreviews[calc.name].deal.sql}
                            </pre>
                          </div>
                        )}
                        
                        {existingSqlPreviews[calc.name].tranche && (
                          <div>
                            <div className="text-xs text-gray-400 mb-2 font-medium">Tranche Level SQL:</div>
                            <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
                              {existingSqlPreviews[calc.name].tranche.sql}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-gray-400 text-sm py-4">
                        Failed to load SQL preview
                      </div>
                    )}
                    
                    <div className="mt-3 p-2 bg-blue-900 rounded text-xs text-blue-200">
                      <strong>💡 Note:</strong> This subquery is combined with others using LEFT JOINs in the final report query.
                      Group level: <span className="font-semibold">{calc.group_level}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalculationBuilder;