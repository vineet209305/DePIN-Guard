import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './HistoryPage.css';

const HistoryPage = () => {
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [searchTerm, setSearchTerm]   = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  const fetchHistory = async () => {
    try {
      const res = await authenticatedFetch('/api/history/all');
      if (!res) return;
      const data = await res.json();

      if (data && data.history && data.history.length > 0) {
        setHistoryData(prev => {
          const existingIds = new Set(prev.map(h => h.id));
          const newEntries = data.history.filter(h => !existingIds.has(h.id));
          return [...data.history, ...prev.filter(h => !data.history.find(d => d.id === h.id))];
        });
      }
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'normal':   return { bg: '#22c55e20', text: '#22c55e' };
      case 'critical': return { bg: '#ef444420', text: '#ef4444' };
      case 'verified': return { bg: '#22c55e20', text: '#22c55e' };
      case 'pending':  return { bg: '#f59e0b20', text: '#f59e0b' };
      case 'failed':   return { bg: '#ef444420', text: '#ef4444' };
      default:         return { bg: '#6b728020', text: '#6b7280' };
    }
  };

  const filteredData = historyData.filter(item => {
    const matchesSearch =
      (item.device ?? '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.hash   ?? '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || item.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const totalPages  = Math.ceil(filteredData.length / itemsPerPage);
  const startIndex  = (currentPage - 1) * itemsPerPage;
  const currentData = filteredData.slice(startIndex, startIndex + itemsPerPage);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) setCurrentPage(page);
  };

  useEffect(() => { setCurrentPage(1); }, [filterStatus, searchTerm]);

  const handleExportCSV = () => {
    const headers  = ['ID', 'Device', 'Hash', 'Value', 'Timestamp', 'Status'];
    const csvData  = filteredData.map(item => [
      item.id, item.device, item.hash, item.value ?? item.temp, item.timestamp, item.status
    ]);
    const csvContent = [headers.join(','), ...csvData.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url  = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `iot-history-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const statuses = [...new Set(historyData.map(h => h.status))];

  return (
    <Layout>
      <div className="history-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Data History</h1>
            <p className="page-subtitle">View all blockchain-verified device data</p>
          </div>
          <button className="export-button" onClick={handleExportCSV}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </button>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <div className="search-box">
            <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search by device or hash..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filterStatus === 'all' ? 'active' : ''}`}
              onClick={() => setFilterStatus('all')}
            >
              All ({historyData.length})
            </button>
            {statuses.map(s => (
              <button
                key={s}
                className={`filter-btn ${filterStatus === s ? 'active' : ''}`}
                onClick={() => setFilterStatus(s)}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)} ({historyData.filter(h => h.status === s).length})
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="table-container">
          <div className="table-wrapper">
            {loading ? (
              <p style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                Loading history...
              </p>
            ) : historyData.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                No history yet — start the simulator!
              </p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Device</th>
                    <th>Hash</th>
                    <th>Temp</th>
                    <th>Vibration</th>
                    <th>Power</th>
                    <th>Timestamp</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {currentData.map((item, i) => (
                    <tr key={item.id ?? i}>
                      <td>#{item.id}</td>
                      <td>
                        <div className="device-cell">
                          <div className="device-icon-small">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                              <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                            </svg>
                          </div>
                          <span>{item.device}</span>
                        </div>
                      </td>
                      <td><code className="hash-code">{item.hash ?? '---'}</code></td>
                      <td><span className="value-badge">{item.temp ?? '—'}°C</span></td>
                      <td><span className="value-badge">{item.vib  ?? '—'}</span></td>
                      <td><span className="value-badge">{item.pwr  ?? '—'}W</span></td>
                      <td>{item.timestamp}</td>
                      <td>
                        <span
                          className="status-badge-table"
                          style={{
                            background: getStatusColor(item.status).bg,
                            color:      getStatusColor(item.status).text,
                          }}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {filteredData.length === 0 && !loading && historyData.length > 0 && (
            <div className="no-data">
              <p>No data found matching your search.</p>
            </div>
          )}
        </div>

        {/* Pagination */}
        {filteredData.length > itemsPerPage && (
          <div className="pagination">
            <button
              className="pagination-button"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <div className="page-numbers">
              {[...Array(Math.min(5, totalPages))].map((_, index) => {
                let pageNum;
                if (totalPages <= 5)          pageNum = index + 1;
                else if (currentPage <= 3)    pageNum = index + 1;
                else if (currentPage >= totalPages - 2) pageNum = totalPages - 4 + index;
                else                          pageNum = currentPage - 2 + index;
                return (
                  <button
                    key={pageNum}
                    className={`page-number ${currentPage === pageNum ? 'active' : ''}`}
                    onClick={() => handlePageChange(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <button
              className="pagination-button"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        )}

        {filteredData.length > 0 && (
          <div className="results-info">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredData.length)} of {filteredData.length} entries
          </div>
        )}
      </div>
    </Layout>
  );
};

export default HistoryPage;