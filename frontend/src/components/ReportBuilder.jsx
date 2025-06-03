import React, { useState, useEffect } from 'react';
import { Play, Filter, BarChart3, FileText, Download, Clock, CheckCircle } from 'lucide-react';

const ReportBuilder = () => {
  const [reportData, setReportData] = useState({
    report_name: '',
    aggregation_level: 'deal',
    selected_deals: [],
    selected_tranches: [],
    cycle_code: '',
    calculations: [],
    filters: {}
  });

  const [availableOptions, setAvailableOptions] = useState({
    deals: [],
    tranches: [],
    cycles: [],
    calculations: []
  });

  const [reportResult, setReportResult] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAvailableOptions();
  }, []);

  useEffect(() => {
    // Fetch tranches when deals are selected
    if (reportData.selected_deals.length > 0) {
      fetchTranches(reportData.selected_deals);
    } else {
      setAvailableOptions(prev => ({ ...prev, tranches: [] }));
      setReportData(prev => ({ ...prev, selected_tranches: [] }));
    }
  }, [reportData.selected_deals]);

  const fetchAvailableOptions = async () => {
    try {
      const [dealsRes, cyclesRes, calculationsRes] = await Promise.all([
        fetch('/api/reports/deals'),
        fetch('/api/reports/cycles'),
        fetch('/api/reports/calculations')
      ]);

      const [deals, cycles, calculations] = await Promise.all([
        dealsRes.json(),
        cyclesRes.json(),
        calculationsRes.json()
      ]);

      setAvailableOptions(prev => ({
        ...prev,
        deals,
        cycles,
        calculations
      }));
    } catch (error) {
      console.error('Error fetching options:', error);
      setError('Failed to load available options');
    }
  };

  const fetchTranches = async (dealNumbers) => {
    try {
      const response = await fetch(`/api/reports/tranches?deal_numbers=${dealNumbers.join(',')}`);
      const tranches = await response.json();
      setAvailableOptions(prev => ({ ...prev, tranches }));
    } catch (error) {
      console.error('Error fetching tranches:', error);
    }
  };

  const handleDealSelection = (dlNbr) => {
    const newDeals = reportData.selected_deals.includes(dlNbr)
      ? reportData.selected_deals.filter(d => d !== dlNbr)
      : [...reportData.selected_deals, dlNbr];
    
    setReportData(prev => ({ ...prev, selected_deals: newDeals }));
  };

  const handleTrancheSelection = (trId) => {
    const newTranches = reportData.selected_tranches.includes(trId)
      ? reportData.selected_tranches.filter(t => t !== trId)
      : [...reportData.selected_tranches, trId];
    
    setReportData(prev => ({ ...prev, selected_tranches: newTranches }));
  };

  const handleCalculationSelection = (calcName) => {
    const newCalcs = reportData.calculations.includes(calcName)
      ? reportData.calculations.filter(c => c !== calcName)
      : [...reportData.calculations, calcName];
    
    setReportData(prev => ({ ...prev, calculations: newCalcs }));
  };

  const validateReport = () => {
    const errors = [];
    if (!reportData.report_name.trim()) errors.push('Report name is required');
    if (reportData.selected_deals.length === 0) errors.push('At least one deal must be selected');
    if (reportData.selected_tranches.length === 0) errors.push('At least one tranche must be selected');
    if (!reportData.cycle_code) errors.push('Cycle code must be selected');
    if (reportData.calculations.length === 0) errors.push('At least one calculation must be selected');
    
    return errors;
  };

  const generateReport = async () => {
    const validationErrors = validateReport();
    if (validationErrors.length > 0) {
      setError(validationErrors.join(', '));
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData),
      });

      if (response.ok) {
        const result = await response.json();
        setReportResult(result);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to generate report');
      }
    } catch (error) {
      console.error('Error generating report:', error);
      setError('Network error while generating report');
    } finally {
      setIsGenerating(false);
    }
  };

  const exportReport = (format) => {
    if (!reportResult) return;

    let content;
    let filename;
    let mimeType;

    if (format === 'csv') {
      const headers = ['Deal Number (dl_nbr)'];
      if (reportData.aggregation_level === 'tranche') {
        headers.push('Tranche ID (tr_id)');
      }
      headers.push(...reportResult.columns);

      const csvRows = [headers.join(',')];
      
      reportResult.data.forEach(row => {
        const rowData = [row.dl_nbr];
        if (reportData.aggregation_level === 'tranche') {
          rowData.push(row.tr_id || '');
        }
        reportResult.columns.forEach(col => {
          rowData.push(row.values[col] || '');
        });
        csvRows.push(rowData.join(','));
      });

      content = csvRows.join('\n');
      filename = `${reportResult.report_name}.csv`;
      mimeType = 'text/csv';
    } else {
      content = JSON.stringify(reportResult, null, 2);
      filename = `${reportResult.report_name}.json`;
      mimeType = 'application/json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="h-8 w-8 text-green-600" />
          <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Report Configuration */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 text-gray-800">Report Configuration</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Report Name *
                  </label>
                  <input
                    type="text"
                    value={reportData.report_name}
                    onChange={(e) => setReportData(prev => ({ ...prev, report_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Q4 Deal Analysis"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Aggregation Level *
                  </label>
                  <select
                    value={reportData.aggregation_level}
                    onChange={(e) => setReportData(prev => ({ ...prev, aggregation_level: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="deal">Deal Level</option>
                    <option value="tranche">Tranche Level</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cycle Code *
                </label>
                <select
                  value={reportData.cycle_code}
                  onChange={(e) => setReportData(prev => ({ ...prev, cycle_code: parseInt(e.target.value) || '' }))}
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
            </div>

            {/* Deal Selection */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                Select Deals * ({reportData.selected_deals.length} selected)
              </h3>
              <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-md bg-white">
                {availableOptions.deals.map(deal => (
                  <label key={deal.dl_nbr} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100">
                    <input
                      type="checkbox"
                      checked={reportData.selected_deals.includes(deal.dl_nbr)}
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
            {reportData.selected_deals.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">
                  Select Tranches * ({reportData.selected_tranches.length} selected)
                </h3>
                <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-md bg-white">
                  {availableOptions.tranches.map(tranche => (
                    <label key={tranche.tr_id} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100">
                      <input
                        type="checkbox"
                        checked={reportData.selected_tranches.includes(tranche.tr_id)}
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
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                Select Calculations * ({reportData.calculations.length} selected)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {availableOptions.calculations.map(calc => (
                  <label key={calc.name} className="flex items-start p-3 border border-gray-200 rounded-md hover:bg-white cursor-pointer bg-gray-25">
                    <input
                      type="checkbox"
                      checked={reportData.calculations.includes(calc.name)}
                      onChange={() => handleCalculationSelection(calc.name)}
                      className="mr-3 mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div>
                      <div className="font-medium text-gray-900">{calc.name}</div>
                      <div className="text-sm text-gray-500">{calc.description}</div>
                      <div className="text-xs text-blue-600 mt-1">{calc.aggregation_method}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Report Actions & Results */}
          <div className="space-y-6">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Generate Report</h3>
              
              <button
                onClick={generateReport}
                disabled={isGenerating}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? (
                  <>
                    <Clock className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Generate Report
                  </>
                )}
              </button>

              {reportResult && (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Report Generated Successfully</span>
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <div>Rows: {reportResult.row_count}</div>
                    <div>Execution: {reportResult.execution_time_ms?.toFixed(1)}ms</div>
                    <div>Generated: {new Date(reportResult.generated_at).toLocaleString()}</div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => exportReport('csv')}
                      className="flex items-center gap-1 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700 transition-colors"
                    >
                      <Download className="h-3 w-3" />
                      CSV
                    </button>
                    <button
                      onClick={() => exportReport('json')}
                      className="flex items-center gap-1 bg-gray-600 text-white px-3 py-2 rounded text-sm hover:bg-gray-700 transition-colors"
                    >
                      <Download className="h-3 w-3" />
                      JSON
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Report Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">Report Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Level:</span>
                  <span className="font-medium capitalize">{reportData.aggregation_level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Deals:</span>
                  <span className="font-medium">{reportData.selected_deals.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tranches:</span>
                  <span className="font-medium">{reportData.selected_tranches.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Cycle:</span>
                  <span className="font-medium">{reportData.cycle_code || 'None'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Calculations:</span>
                  <span className="font-medium">{reportData.calculations.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Report Results Table */}
        {reportResult && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-800">{reportResult.report_name}</h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Deal Number (dl_nbr)
                    </th>
                    {reportData.aggregation_level === 'tranche' && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tranche ID (tr_id)
                      </th>
                    )}
                    {reportResult.columns.map(col => (
                      <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {col.replace('_', ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {reportResult.data.slice(0, 100).map((row, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {row.dl_nbr}
                      </td>
                      {reportData.aggregation_level === 'tranche' && (
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {row.tr_id}
                        </td>
                      )}
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
              
              {reportResult.data.length > 100 && (
                <div className="text-sm text-gray-500 mt-3 text-center">
                  Showing first 100 rows of {reportResult.row_count} total rows. 
                  Export for complete data.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportBuilder;