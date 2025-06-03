// frontend/src/components/ReportTemplateBuilder.jsx
import React, { useState, useEffect } from 'react';
import { Save, Play, Edit3, Trash2, FileText, Clock, CheckCircle, Calendar, History, Eye, X } from 'lucide-react';

const ReportTemplateBuilder = () => {
  const [templates, setTemplates] = useState([]);
  const [isCreating, setIsCreating] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [reportResult, setReportResult] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [selectedCycle, setSelectedCycle] = useState('');
  const [error, setError] = useState(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    aggregation_level: 'deal',
    selected_deals: [],
    selected_tranches: [],
    selected_calculations: []
  });

  const [availableOptions, setAvailableOptions] = useState({
    deals: [],
    tranches: [],
    cycles: [],
    calculations: []
  });

  useEffect(() => {
    fetchReportTemplates();
    fetchAvailableOptions();
    fetchFilteredCalculations();
  }, []);

  useEffect(() => {
    fetchFilteredCalculations();
  }, [formData.aggregation_level]);

  useEffect(() => {
    if (formData.selected_deals.length > 0) {
      fetchTranches(formData.selected_deals);
    } else {
      setAvailableOptions(prev => ({ ...prev, tranches: [] }));
      setFormData(prev => ({ ...prev, selected_tranches: [] }));
    }
  }, [formData.selected_deals]);

  const fetchReportTemplates = async () => {
    try {
      const response = await fetch('/api/reports/templates');
      if (response.ok) {
        const templates = await response.json();
        setTemplates(templates);
      }
    } catch (error) {
      console.error('Error fetching report templates:', error);
    }
  };

  const fetchAvailableOptions = async () => {
    try {
      const [dealsRes, cyclesRes, tranchesRes] = await Promise.all([
        fetch('/api/datawarehouse/deals'),
        fetch('/api/datawarehouse/cycles'),
        fetch('/api/datawarehouse/tranches')
      ]);

      if (!dealsRes.ok || !cyclesRes.ok || !tranchesRes.ok) {
        throw new Error('Failed to fetch options');
      }

      const [deals, cycles, tranches] = await Promise.all([
        dealsRes.json(),
        cyclesRes.json(),
        tranchesRes.json()
      ]);

      setAvailableOptions(prev => ({
        ...prev,
        deals: Array.isArray(deals) ? deals : [],
        cycles: Array.isArray(cycles) ? cycles : [],
        tranches: Array.isArray(tranches) ? tranches : []
      }));
    } catch (error) {
      console.error('Error fetching options:', error);
      setError('Failed to load available options');
    }
  };

  const fetchFilteredCalculations = async () => {
    try {
      const aggregationLevel = formData.aggregation_level || 'deal';
      const response = await fetch(`/api/calculations?group_level=${aggregationLevel}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch calculations: ${response.status}`);
      }
      
      const filteredCalculations = await response.json();
      setAvailableOptions(prev => ({
        ...prev,
        calculations: Array.isArray(filteredCalculations) ? filteredCalculations : []
      }));

      if (Array.isArray(filteredCalculations)) {
        const availableCalcNames = filteredCalculations.map(calc => calc.name);
        const validSelections = formData.selected_calculations.filter(calcName => 
          availableCalcNames.includes(calcName)
        );
        
        if (validSelections.length !== formData.selected_calculations.length) {
          setFormData(prev => ({ ...prev, selected_calculations: validSelections }));
        }
      }
    } catch (error) {
      console.error('Error fetching calculations:', error);
      setAvailableOptions(prev => ({ ...prev, calculations: [] }));
    }
  };

  const fetchTranches = async (dealNumbers) => {
    try {
      const dealParams = dealNumbers.join(',');
      const response = await fetch(`/api/datawarehouse/tranches?deal_numbers=${dealParams}`);
      if (response.ok) {
        const tranches = await response.json();
        setAvailableOptions(prev => ({ ...prev, tranches: tranches || [] }));
      }
    } catch (error) {
      console.error('Error fetching tranches:', error);
    }
  };

  const handleCreateTemplate = async () => {
    // Validation (no cycle_code needed)
    const validationErrors = [];
    if (!formData.name.trim()) validationErrors.push('Template name is required');
    if (formData.selected_deals.length === 0) validationErrors.push('At least one deal must be selected');
    if (formData.selected_tranches.length === 0) validationErrors.push('At least one tranche must be selected');
    if (formData.selected_calculations.length === 0) validationErrors.push('At least one calculation must be selected');
    
    if (validationErrors.length > 0) {
      setError(validationErrors.join(', '));
      return;
    }

    try {
      // Use PUT for editing existing template, POST for creating new template
      const url = editingTemplate 
        ? `/api/reports/templates/${editingTemplate.id}`
        : '/api/reports/templates';
      
      const method = editingTemplate ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description,
          aggregation_level: formData.aggregation_level,
          selected_deals: formData.selected_deals,
          selected_tranches: formData.selected_tranches,
          selected_calculations: formData.selected_calculations
        }),
      });

      if (response.ok) {
        await fetchReportTemplates();
        handleCancel();
        setError(null);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || `Failed to ${editingTemplate ? 'update' : 'create'} template`);
      }
    } catch (error) {
      console.error(`Error ${editingTemplate ? 'updating' : 'creating'} template:`, error);
      setError(`Error ${editingTemplate ? 'updating' : 'creating'} template`);
    }
  };

  const handleExecuteClick = (template) => {
    setSelectedTemplate(template);
    setSelectedCycle(template.last_executed_cycle || ''); // Pre-select last cycle if available
    setShowExecuteModal(true);
  };

  const handleExecuteTemplate = async () => {
    if (!selectedCycle) {
      setError('Please select a cycle code');
      return;
    }

    setIsExecuting(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/reports/templates/${selectedTemplate.id}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cycle_code: parseInt(selectedCycle) }),
      });

      if (response.ok) {
        const result = await response.json();
        setReportResult(result);
        setShowExecuteModal(false);
        await fetchReportTemplates(); // Refresh to show updated last execution
      } else {
        const error = await response.json();
        setError(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error executing template:', error);
      setError('Error executing template');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm('Are you sure you want to delete this report template?')) {
      return;
    }

    try {
      const response = await fetch(`/api/reports/templates/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchReportTemplates();
      } else {
        const error = await response.json();
        setError(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting template:', error);
      setError('Error deleting template');
    }
  };

  const handleEditTemplate = async (template) => {
    try {
      const response = await fetch(`/api/reports/templates/${template.id}`);
      const templateDetail = await response.json();
      
      setEditingTemplate(template);
      setFormData({
        name: templateDetail.name,
        description: templateDetail.description || '',
        aggregation_level: templateDetail.aggregation_level,
        selected_deals: templateDetail.selected_deals,
        selected_tranches: templateDetail.selected_tranches,
        selected_calculations: templateDetail.selected_calculations
      });
      setIsCreating(true);
    } catch (error) {
      console.error('Error loading template details:', error);
      setError('Error loading template details');
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingTemplate(null);
    setError(null);
    setFormData({
      name: '',
      description: '',
      aggregation_level: 'deal',
      selected_deals: [],
      selected_tranches: [],
      selected_calculations: []
    });
  };

  const handleDealSelection = (dlNbr) => {
    const newDeals = formData.selected_deals.includes(dlNbr)
      ? formData.selected_deals.filter(d => d !== dlNbr)
      : [...formData.selected_deals, dlNbr];
    
    setFormData(prev => ({ ...prev, selected_deals: newDeals }));
  };

  const handleTrancheSelection = (trId) => {
    const newTranches = formData.selected_tranches.includes(trId)
      ? formData.selected_tranches.filter(t => t !== trId)
      : [...formData.selected_tranches, trId];
    
    setFormData(prev => ({ ...prev, selected_tranches: newTranches }));
  };

  const handleCalculationSelection = (calcName) => {
    const newCalcs = formData.selected_calculations.includes(calcName)
      ? formData.selected_calculations.filter(c => c !== calcName)
      : [...formData.selected_calculations, calcName];
    
    setFormData(prev => ({ ...prev, selected_calculations: newCalcs }));
  };

  const handlePreviewSQL = async (template) => {
    setPreviewLoading(true);
    setPreviewData(null);
    setShowPreviewModal(true);
    
    try {
      // Use a sample cycle for preview
      const sampleCycle = availableOptions.cycles.length > 0 ? availableOptions.cycles[0].cycle_cde : 202404;
      const response = await fetch(`/api/reports/templates/${template.id}/preview-sql?cycle_code=${sampleCycle}`);
      
      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error generating SQL preview');
        setShowPreviewModal(false);
      }
    } catch (error) {
      console.error('Error previewing SQL:', error);
      setError('Error generating SQL preview');
      setShowPreviewModal(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Report Templates</h1>
            <span className="text-sm text-gray-500 bg-blue-50 px-2 py-1 rounded">
              Cycle selected at runtime
            </span>
          </div>
          {!isCreating && (
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              <Save className="h-4 w-4" />
              New Template
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Template Creation/Edit Form */}
        {isCreating && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6 border-2 border-blue-200">
            <h2 className="text-xl font-semibold mb-4">
              {editingTemplate ? 'Edit Template' : 'Create New Template'}
            </h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Q4 Deal Analysis Template"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Aggregation Level *
                  </label>
                  <select
                    value={formData.aggregation_level}
                    onChange={(e) => setFormData(prev => ({ ...prev, aggregation_level: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="deal">Deal Level</option>
                    <option value="tranche">Tranche Level</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of this template"
                />
              </div>

              {/* Note about cycle selection */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">Cycle Selection</span>
                </div>
                <p className="text-sm text-blue-700 mt-1">
                  Cycle codes are now selected when executing the template, making templates reusable across different reporting periods.
                </p>
              </div>

              {/* Deal Selection */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">
                  Select Deals * ({formData.selected_deals.length} selected)
                </h3>
                <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-md bg-white">
                  {availableOptions.deals.map(deal => (
                    <label key={deal.dl_nbr} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100">
                      <input
                        type="checkbox"
                        checked={formData.selected_deals.includes(deal.dl_nbr)}
                        onChange={() => handleDealSelection(deal.dl_nbr)}
                        className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <div>
                        <div className="font-medium text-gray-900">{deal.dl_nbr}</div>
                        <div className="text-sm text-gray-500">{deal.issr_cde} - {deal.cdi_file_nme}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Tranche Selection */}
              {formData.selected_deals.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-4 text-gray-800">
                    Select Tranches * ({formData.selected_tranches.length} selected)
                  </h3>
                  <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-md bg-white">
                    {availableOptions.tranches.map(tranche => (
                      <label key={`${tranche.dl_nbr}-${tranche.tr_id}`} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100">
                        <input
                          type="checkbox"
                          checked={formData.selected_tranches.includes(tranche.tr_id)}
                          onChange={() => handleTrancheSelection(tranche.tr_id)}
                          className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <div>
                          <div className="font-medium text-gray-900">{tranche.tr_id}</div>
                          <div className="text-sm text-gray-500">{tranche.tr_cusip_id} (Deal: {tranche.dl_nbr})</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Calculation Selection */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2 text-gray-800">
                  Select Calculations * ({formData.selected_calculations.length} selected)
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Showing calculations available for <span className="font-medium capitalize">{formData.aggregation_level}</span> level reporting
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Array.isArray(availableOptions.calculations) && availableOptions.calculations.map(calc => (
                    <label key={calc.name} className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-white cursor-pointer bg-gray-25">
                      <input
                        type="checkbox"
                        checked={formData.selected_calculations.includes(calc.name)}
                        onChange={() => handleCalculationSelection(calc.name)}
                        className="mr-3 mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <div>
                        <div className="font-medium text-gray-900">{calc.name}</div>
                        <div className="text-sm text-gray-500">{calc.description}</div>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="text-xs text-blue-600">{calc.aggregation_function}</div>
                          <div className={`text-xs px-1 py-0.5 rounded ${
                            calc.group_level === 'deal' ? 'bg-green-100 text-green-700' :
                            calc.group_level === 'tranche' ? 'bg-purple-100 text-purple-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {calc.group_level === 'deal' ? 'Deal' : 'Tranche'}
                          </div>
                          <div className="text-xs text-gray-500">{calc.source_model}.{calc.source_field}</div>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
                {availableOptions.calculations.length === 0 && (
                  <div className="text-gray-500 text-center py-4">
                    No calculations available for {formData.aggregation_level} level. 
                    <br />Check the Calculations tab to create some first.
                  </div>
                )}
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCreateTemplate}
                  className="flex items-center gap-2 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
                >
                  <Save className="h-4 w-4" />
                  {editingTemplate ? 'Update Template' : 'Save Template'}
                </button>
                <button
                  onClick={handleCancel}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Execute Modal */}
        {showExecuteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96 max-w-90vw">
              <h3 className="text-lg font-semibold mb-4">Execute Report Template</h3>
              <p className="text-gray-600 mb-4">
                Template: <span className="font-medium">{selectedTemplate?.name}</span>
              </p>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Cycle Code *
                </label>
                <select
                  value={selectedCycle}
                  onChange={(e) => setSelectedCycle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select cycle code...</option>
                  {availableOptions.cycles.map(cycle => (
                    <option key={cycle.cycle_cde} value={cycle.cycle_cde}>
                      {cycle.cycle_cde}
                    </option>
                  ))}
                </select>
              </div>

              {selectedTemplate?.last_executed_cycle && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
                  <div className="flex items-center gap-2">
                    <History className="h-4 w-4 text-blue-600" />
                    <span className="text-sm text-blue-800">
                      Last executed: {selectedTemplate.last_executed_cycle}
                    </span>
                  </div>
                </div>
              )}
              
              <div className="flex gap-3">
                <button
                  onClick={handleExecuteTemplate}
                  disabled={isExecuting || !selectedCycle}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isExecuting ? (
                    <>
                      <Clock className="h-4 w-4 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Execute
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowExecuteModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Report Templates List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Saved Templates</h2>
          {templates.map((template) => (
            <div key={template.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      template.aggregation_level === 'deal' ? 'bg-green-100 text-green-800' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {template.aggregation_level === 'deal' ? 'Deal Level' : 'Tranche Level'}
                    </span>
                  </div>
                  {template.description && (
                    <p className="text-gray-600 mb-2">{template.description}</p>
                  )}
                  <div className="flex gap-4 text-sm text-gray-500 mb-2">
                    <span>Deals: {template.deal_count}</span>
                    <span>Tranches: {template.tranche_count}</span>
                    <span>Calculations: {template.calculation_count}</span>
                    {template.last_executed_cycle && (
                      <span className="text-blue-600 font-medium">
                        Last run: {template.last_executed_cycle}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400">
                    Created: {new Date(template.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handlePreviewSQL(template)}
                    className="flex items-center gap-1 bg-indigo-600 text-white px-3 py-2 rounded text-sm hover:bg-indigo-700"
                    title="Preview SQL"
                  >
                    <Eye className="h-3 w-3" />
                    SQL
                  </button>
                  <button
                    onClick={() => handleExecuteClick(template)}
                    disabled={isExecuting}
                    className="flex items-center gap-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    <Play className="h-3 w-3" />
                    Execute
                  </button>
                  <button
                    onClick={() => handleEditTemplate(template)}
                    className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-md"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteTemplate(template.id)}
                    className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Report Results Display */}
        {reportResult && (
          <div className="mt-6 bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <h3 className="text-lg font-semibold text-gray-800">{reportResult.report_name}</h3>
              <span className="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded">
                Cycle: {reportResult.cycle_code}
              </span>
            </div>
            
            <div className="text-sm text-gray-600 space-y-1 mb-4">
              <div>Template ID: {reportResult.report_id}</div>
              <div>Aggregation: {reportResult.aggregation_level}</div>
              <div>Rows: {reportResult.row_count}</div>
              <div>Execution: {reportResult.execution_time_ms?.toFixed(1)}ms</div>
              <div>Generated: {new Date(reportResult.generated_at).toLocaleString()}</div>
            </div>

            {/* Results table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Deal Number
                    </th>
                    {reportResult.aggregation_level === 'tranche' && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Tranche ID
                      </th>
                    )}
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Cycle Code
                    </th>
                    {reportResult.columns.map(col => (
                      <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportResult.data.slice(0, 50).map((row, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {row.dl_nbr}
                      </td>
                      {reportResult.aggregation_level === 'tranche' && (
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {row.tr_id}
                        </td>
                      )}
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {row.cycle_cde}
                      </td>
                      {reportResult.columns.map(col => (
                        <td key={col} className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {typeof row.values[col] === 'number' 
                            ? row.values[col].toLocaleString()
                            : row.values[col] || '-'
                          }
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* SQL Preview Modal */}
      {showPreviewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Report Template SQL Preview</h2>
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
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Template Details</h3>
                      <div className="bg-gray-50 rounded p-3 text-sm">
                        <p><strong>Name:</strong> {previewData.template_name}</p>
                        <p><strong>Level:</strong> {previewData.aggregation_level}</p>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Parameters</h3>
                      <div className="bg-gray-50 rounded p-3 text-sm">
                        <p><strong>Cycle:</strong> {previewData.parameters?.cycle_code}</p>
                        <p><strong>Deals:</strong> {previewData.parameters?.deal_numbers?.length || 0} selected</p>
                        <p><strong>Tranches:</strong> {previewData.parameters?.tranche_ids?.length || 0} selected</p>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Raw Execution SQL</h3>
                    <div className="bg-gray-900 text-green-400 rounded p-4 overflow-x-auto">
                      <pre className="text-sm font-mono whitespace-pre-wrap">{previewData.sql_query}</pre>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      This is the exact same SQL that executes when this report template runs.
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

export default ReportTemplateBuilder;