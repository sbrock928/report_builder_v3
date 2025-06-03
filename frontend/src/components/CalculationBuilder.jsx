// frontend/src/components/CalculationBuilder.jsx
import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, Edit3, Calculator, Database, Eye, X } from 'lucide-react';
import { useNotification } from './NotificationSystem';

const CalculationBuilder = () => {
  const [calculations, setCalculations] = useState([]);
  const [filteredCalculations, setFilteredCalculations] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [editingCalculation, setEditingCalculation] = useState(null);
  const [error, setError] = useState(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [calculation, setCalculation] = useState({
    name: '',
    function_type: 'SUM',
    source: '',
    level: 'deal',
    weight_field: '',
    description: ''
  });
  const [allAvailableFields, setAllAvailableFields] = useState({});
  const [aggregationFunctions, setAggregationFunctions] = useState([]);
  const [sourceModels, setSourceModels] = useState([]);
  const [groupLevels, setGroupLevels] = useState([]);
  const [fieldsLoading, setFieldsLoading] = useState(false);
  const { success, error: showError } = useNotification();
  
  // Available options for the ORM-based system (removed - now fetched from API)

  // Fetch calculation configuration from API
  const fetchCalculationConfig = async () => {
    setFieldsLoading(true);
    try {
      const response = await fetch('/api/calculations/configuration');
      
      if (!response.ok) {
        throw new Error('Failed to fetch calculation configuration');
      }

      const result = await response.json();
      const data = result.data || {};
      
      // Set all configuration data from API
      setAllAvailableFields(data.field_mappings || {});
      setAggregationFunctions(data.aggregation_functions || []);
      setSourceModels(data.source_models || []);
      setGroupLevels(data.group_levels || []);
    } catch (error) {
      console.error('Error fetching calculation configuration:', error);
      showError('Error loading calculation configuration. Using default settings.');
      
      // Fallback to hardcoded configuration if API fails
      setAllAvailableFields({
        'Deal': [
          { value: 'dl_nbr', label: 'Deal Number', type: 'number' }
        ],
        'Tranche': [
          { value: 'tr_id', label: 'Tranche ID', type: 'string' },
          { value: 'dl_nbr', label: 'Deal Number', type: 'number' }
        ],
        'TrancheBal': [
          { value: 'tr_end_bal_amt', label: 'Ending Balance Amount', type: 'currency' },
          { value: 'tr_pass_thru_rte', label: 'Pass Through Rate', type: 'percentage' },
          { value: 'tr_accrl_days', label: 'Accrual Days', type: 'number' },
          { value: 'tr_int_dstrb_amt', label: 'Interest Distribution Amount', type: 'currency' },
          { value: 'tr_prin_dstrb_amt', label: 'Principal Distribution Amount', type: 'currency' },
          { value: 'tr_int_accrl_amt', label: 'Interest Accrual Amount', type: 'currency' },
          { value: 'tr_int_shtfl_amt', label: 'Interest Shortfall Amount', type: 'currency' },
          { value: 'cycle_cde', label: 'Cycle Code', type: 'number' }
        ]
      });
      
      setAggregationFunctions([
        { value: 'SUM', label: 'SUM - Total amount', description: 'Add all values together' },
        { value: 'AVG', label: 'AVG - Average', description: 'Calculate average value' },
        { value: 'COUNT', label: 'COUNT - Count records', description: 'Count number of records' },
        { value: 'MIN', label: 'MIN - Minimum value', description: 'Find minimum value' },
        { value: 'MAX', label: 'MAX - Maximum value', description: 'Find maximum value' },
        { value: 'WEIGHTED_AVG', label: 'WEIGHTED_AVG - Weighted average', description: 'Calculate weighted average using specified weight field' }
      ]);
      
      setSourceModels([
        { value: 'Deal', label: 'Deal', description: 'Base deal information' },
        { value: 'Tranche', label: 'Tranche', description: 'Tranche structure data' },
        { value: 'TrancheBal', label: 'TrancheBal', description: 'Tranche balance and performance data' }
      ]);
      
      setGroupLevels([
        { value: 'deal', label: 'Deal Level', description: 'Aggregate to deal level' },
        { value: 'tranche', label: 'Tranche Level', description: 'Aggregate to tranche level' }
      ]);
    } finally {
      setFieldsLoading(false);
    }
  };

  // Get available fields for a source model
  const getAvailableFields = (sourceModel) => {
    return allAvailableFields[sourceModel] || [];
  };

  useEffect(() => {
    fetchCalculations();
    fetchCalculationConfig();
  }, []);

  useEffect(() => {
    filterCalculations();
  }, [calculations, selectedFilter]);

  const fetchCalculations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/calculations');
      
      if (!response.ok) {
        throw new Error('Failed to fetch calculations');
      }

      const data = await response.json();
      setCalculations(data);
    } catch (error) {
      console.error('Error fetching calculations:', error);
      showError('Error loading calculations. Please refresh the page.');
    } finally {
      setIsLoading(false);
    }
  };

  const filterCalculations = () => {
    let filtered = calculations;
    
    if (selectedFilter === 'deal') {
      filtered = calculations.filter(calc => calc.group_level === 'deal');
    } else if (selectedFilter === 'tranche') {
      filtered = calculations.filter(calc => calc.group_level === 'tranche');
    }
    
    setFilteredCalculations(filtered);
  };

  const handlePreviewSQL = async (calcId) => {
    setPreviewLoading(true);
    setPreviewData(null);
    setShowPreviewModal(true);
    
    try {
      const response = await fetch(`/api/calculations/${calcId}/preview-sql?group_level=deal&sample_deals=101,102,103&sample_tranches=A,B&sample_cycle=202404`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate SQL preview');
      }

      const data = await response.json();
      setPreviewData(data);
    } catch (error) {
      console.error('Error generating SQL preview:', error);
      showError(`Error generating SQL preview: ${error.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleOpenModal = (calc = null) => {
    if (calc) {
      // Edit mode
      setEditingCalculation(calc);
      setCalculation({
        name: calc.name,
        description: calc.description || '',
        function_type: calc.aggregation_function,
        source: calc.source_model,
        source_field: calc.source_field,
        level: calc.group_level,
        weight_field: calc.weight_field || ''
      });
    } else {
      // Create mode
      setEditingCalculation(null);
      setCalculation({
        name: '',
        function_type: 'SUM',
        source: '',
        source_field: '',
        level: 'deal',
        weight_field: '',
        description: ''
      });
    }
    setError(null);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingCalculation(null);
    setError(null);
    setCalculation({
      name: '',
      function_type: 'SUM',
      source: '',
      source_field: '',
      level: 'deal',
      weight_field: '',
      description: ''
    });
  };

  const handleSaveCalculation = async () => {
    if (!calculation.name || !calculation.function_type || !calculation.source || !calculation.source_field) {
      setError('Please fill in all required fields (Name, Function Type, Source, and Source Field)');
      return;
    }

    if (calculation.function_type === 'WEIGHTED_AVG' && !calculation.weight_field) {
      setError('Weight field is required for weighted average calculations');
      return;
    }

    setIsSaving(true);
    try {
      // Map frontend field names to backend expected field names
      const payload = {
        name: calculation.name,
        description: calculation.description,
        aggregation_function: calculation.function_type,
        source_model: calculation.source,
        source_field: calculation.source_field,
        group_level: calculation.level,
        weight_field: calculation.weight_field || null
      };

      const url = editingCalculation ? `/api/calculations/${editingCalculation.id}` : '/api/calculations';
      const method = editingCalculation ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${editingCalculation ? 'update' : 'save'} calculation`);
      }

      const savedCalculation = await response.json();
      success(`Calculation "${savedCalculation.name}" ${editingCalculation ? 'updated' : 'saved'} successfully!`);
      
      // Close modal and refresh calculations list
      handleCloseModal();
      fetchCalculations();
    } catch (error) {
      console.error('Error saving calculation:', error);
      setError(error.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCalculation = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/calculations/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete calculation');
      }

      success(`Calculation "${name}" deleted successfully!`);
      fetchCalculations();
    } catch (error) {
      console.error('Error deleting calculation:', error);
      showError(`Error deleting calculation: ${error.message}`);
    }
  };

  const getPreviewFormula = () => {
    if (!calculation.function_type || !calculation.source_field) {
      return 'Select aggregation function and field to see preview';
    }

    const field = `${calculation.source}.${calculation.source_field}`;
    
    if (calculation.function_type === 'WEIGHTED_AVG') {
      const weightField = calculation.weight_field ? `${calculation.source}.${calculation.weight_field}` : '[weight_field]';
      return `SUM(${field} * ${weightField}) / NULLIF(SUM(${weightField}), 0)`;
    }
    
    return `${calculation.function_type}(${field})`;
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ORM Calculation Builder</h1>
        </div>
        <button
          onClick={() => handleOpenModal()}
          disabled={fieldsLoading}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
        >
          <Plus className="h-4 w-4" />
          New Calculation
        </button>
      </div>

      {/* Filter and Sort Section */}
      <div className="bg-white rounded-lg p-6 mb-6 border-2 border-blue-200">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Filter Calculations</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Group Level
            </label>
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All</option>
              <option value="deal">Deal Level</option>
              <option value="tranche">Tranche Level</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Filter calculations by their group level
            </p>
          </div>
        </div>
      </div>

      {/* Available Calculations List */}
      <div>
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Available Calculations</h2>
        
        {isLoading || fieldsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">
              {isLoading ? 'Loading calculations...' : 'Loading configuration...'}
            </span>
          </div>
        ) : (
          <div className="grid gap-4">
            {(selectedFilter === 'all' ? calculations : filteredCalculations).map((calc) => (
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
                      onClick={() => handlePreviewSQL(calc.id)}
                      className="flex items-center gap-1 bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 transition-colors"
                      title="Preview SQL"
                    >
                      <Eye className="h-3 w-3" />
                      SQL
                    </button>
                    <button
                      onClick={() => handleOpenModal(calc)}
                      className="flex items-center gap-1 bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700 transition-colors"
                      title="Edit"
                    >
                      <Edit3 className="h-3 w-3" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteCalculation(calc.id, calc.name)}
                      className="flex items-center gap-1 bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            {(selectedFilter === 'all' ? calculations : filteredCalculations).length === 0 && !isLoading && !fieldsLoading && (
              <div className="text-center py-8 text-gray-500">
                No calculations available. Create your first calculation above.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create/Edit Calculation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingCalculation ? 'Edit Calculation' : 'Create New Calculation'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
              {fieldsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600">Loading calculation configuration...</span>
                </div>
              ) : (
                <>
                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
                      {error}
                    </div>
                  )}

              <div className="space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Calculation Name *
                    </label>
                    <input
                      type="text"
                      value={calculation.name}
                      onChange={(e) => setCalculation({ ...calculation, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Total Ending Balance"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Group Level *
                    </label>
                    <select
                      value={calculation.level}
                      onChange={(e) => setCalculation({ ...calculation, level: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {groupLevels.map(level => (
                        <option key={level.value} value={level.value}>
                          {level.label}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {groupLevels.find(l => l.value === calculation.level)?.description}
                    </p>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={calculation.description}
                    onChange={(e) => setCalculation({ ...calculation, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                    placeholder="Describe what this calculation measures..."
                  />
                </div>

                {/* Source Configuration */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Source Model *
                    </label>
                    <select
                      value={calculation.source}
                      onChange={(e) => setCalculation({ ...calculation, source: e.target.value, source_field: '' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select a source model...</option>
                      {sourceModels.map(model => (
                        <option key={model.value} value={model.value}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {sourceModels.find(m => m.value === calculation.source)?.description}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Aggregation Function *
                    </label>
                    <select
                      value={calculation.function_type}
                      onChange={(e) => setCalculation({ ...calculation, function_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {aggregationFunctions.map(func => (
                        <option key={func.value} value={func.value}>
                          {func.label}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      {aggregationFunctions.find(f => f.value === calculation.function_type)?.description}
                    </p>
                  </div>
                </div>

                {/* Field Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Source Field *
                    </label>
                    {fieldsLoading ? (
                      <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                        <span className="text-gray-500">Loading fields...</span>
                      </div>
                    ) : (
                      <select
                        value={calculation.source_field}
                        onChange={(e) => setCalculation({ ...calculation, source_field: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={!calculation.source || getAvailableFields(calculation.source).length === 0}
                      >
                        <option value="">Select a field...</option>
                        {getAvailableFields(calculation.source).map(field => (
                          <option key={field.value} value={field.value}>
                            {field.label} ({field.type})
                          </option>
                        ))}
                      </select>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      {calculation.source ? `Available fields from ${calculation.source} model` : 'Select a source model first'}
                    </p>
                    {/* Show field description if available */}
                    {calculation.source_field && getAvailableFields(calculation.source).find(f => f.value === calculation.source_field)?.description && (
                      <p className="text-xs text-blue-600 mt-1">
                        {getAvailableFields(calculation.source).find(f => f.value === calculation.source_field).description}
                      </p>
                    )}
                  </div>

                  {/* Weight Field for Weighted Average */}
                  {calculation.function_type === 'WEIGHTED_AVG' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Weight Field *
                      </label>
                      {fieldsLoading ? (
                        <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                          <span className="text-gray-500">Loading fields...</span>
                        </div>
                      ) : (
                        <select
                          value={calculation.weight_field}
                          onChange={(e) => setCalculation({ ...calculation, weight_field: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          disabled={!calculation.source || getAvailableFields(calculation.source).length === 0}
                        >
                          <option value="">Select weight field...</option>
                          {getAvailableFields(calculation.source).filter(f => f.type === 'currency' || f.type === 'number').map(field => (
                            <option key={field.value} value={field.value}>
                              {field.label}
                            </option>
                          ))}
                        </select>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        Field to use as weight for the weighted average calculation
                      </p>
                      {/* Show weight field description if available */}
                      {calculation.weight_field && getAvailableFields(calculation.source).find(f => f.value === calculation.weight_field)?.description && (
                        <p className="text-xs text-blue-600 mt-1">
                          {getAvailableFields(calculation.source).find(f => f.value === calculation.weight_field).description}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* ORM Formula Preview */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Generated ORM Formula Preview
                  </label>
                  <div className="bg-gray-100 rounded p-3 border">
                    <code className="text-sm text-gray-800 font-mono">{getPreviewFormula()}</code>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    <strong>Model:</strong> {calculation.source} | 
                    <strong> Function:</strong> {calculation.function_type} | 
                    <strong> Level:</strong> {calculation.level}
                  </div>
                </div>
                                </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={handleCloseModal}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={isSaving || fieldsLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCalculation}
                disabled={isSaving || fieldsLoading}
                className="flex items-center gap-2 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    {editingCalculation ? 'Update Calculation' : 'Save Calculation'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SQL Preview Modal */}
      {showPreviewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">SQL Preview</h2>
              <button
                onClick={() => setShowPreviewModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {previewLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600">Generating SQL preview...</span>
                </div>
              ) : previewData ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Calculation Details</h3>
                      <div className="bg-gray-50 rounded p-3 text-sm">
                        <p><strong>Name:</strong> {previewData.calculation_name}</p>
                        <p><strong>Level:</strong> {previewData.aggregation_level}</p>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Sample Parameters</h3>
                      <div className="bg-gray-50 rounded p-3 text-sm">
                        <p><strong>Deals:</strong> {previewData.sample_parameters?.deals?.join(', ') || 'N/A'}</p>
                        <p><strong>Tranches:</strong> {previewData.sample_parameters?.tranches?.join(', ') || 'N/A'}</p>
                        <p><strong>Cycle:</strong> {previewData.sample_parameters?.cycle || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Raw Execution SQL</h3>
                    <div className="bg-gray-900 text-green-400 rounded p-4 overflow-x-auto">
                      <pre className="text-sm font-mono whitespace-pre-wrap">{previewData.generated_sql}</pre>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      This is the exact same SQL that executes when this calculation runs in a report.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No preview data available
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalculationBuilder;