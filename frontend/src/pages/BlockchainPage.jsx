import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './BlockchainPage.css';

const BlockchainPage = () => {
  const [blocks, setBlocks]           = useState([]);
  const [stats, setStats]             = useState({ totalBlocks: 0, transactions: 0 });
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [loading, setLoading]         = useState(true);

  // ✅ Backend se real blockchain data fetch karo
  const fetchBlockchainData = async () => {
    try {
      const res = await authenticatedFetch('/api/blockchain');
      if (!res) return;
      const data = await res.json();

      if (data) {
        // Stats update karo
        setStats({
          totalBlocks:  data.total_blocks  ?? data.totalBlocks  ?? 0,
          transactions: data.transactions  ?? 0,
        });

        // Blocks update karo — recent_blocks use karo
        if (data.recent_blocks && data.recent_blocks.length > 0) {
          setBlocks(prev => {
            // Purane blocks ke saath merge karo — duplicates hata ke
            const existingIds = new Set(prev.map(b => b.id));
            const newBlocks = data.recent_blocks.filter(b => !existingIds.has(b.id));
            return [...newBlocks, ...prev].slice(0, 50); // max 50 blocks store
          });
        }
      }
    } catch (err) {
      console.log('Blockchain API not available:', err);
    } finally {
      setLoading(false);
    }
  };

  // Page load pe fetch + har 5 second mein refresh
  useEffect(() => {
    fetchBlockchainData();
    const interval = setInterval(fetchBlockchainData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSync = () => fetchBlockchainData();

  return (
    <Layout>
      <div className="blockchain-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">Blockchain Explorer</h1>
            <p className="page-subtitle">Real-time network throughput and block data</p>
          </div>
          <button className="sync-button" onClick={handleSync}>Sync Network</button>
        </div>

        {/* Stats */}
        <div className="blockchain-stats-grid">
          <div className="stat-card-blockchain">
            <div className="stat-content-blockchain">
              <div className="stat-value-blockchain">
                {loading ? '...' : stats.totalBlocks.toLocaleString()}
              </div>
              <div className="stat-label-blockchain">Total Blocks</div>
            </div>
          </div>
          <div className="stat-card-blockchain">
            <div className="stat-content-blockchain">
              <div className="stat-value-blockchain">
                {loading ? '...' : stats.transactions.toLocaleString()}
              </div>
              <div className="stat-label-blockchain">Total Transactions</div>
            </div>
          </div>
        </div>

        {/* Blocks List */}
        <div className="blocks-section">
          {loading ? (
            <p style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
              Loading blockchain data...
            </p>
          ) : blocks.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
              No blocks yet — start the simulator to generate transactions!
            </p>
          ) : (
            <div className="blocks-list">
              {blocks.map((block, i) => (
                <div key={block.id ?? i} className="block-card">
                  <div className="block-header">
                    <div className="block-height">Block #{block.id}</div>
                    <span className="block-status confirmed">{block.status ?? 'Confirmed'}</span>
                  </div>
                  <div className="block-info-grid">
                    <div className="info-item">
                      <div className="info-label">Hash</div>
                      <code className="info-value">
                        {block.hash ? block.hash.substring(0, 20) + '...' : '—'}
                      </code>
                    </div>
                    <div className="info-item">
                      <div className="info-label">Prev Hash</div>
                      <code className="info-value">
                        {block.prev_hash ? block.prev_hash.substring(0, 20) + '...' : '—'}
                      </code>
                    </div>
                    <div className="info-item">
                      <div className="info-label">Timestamp</div>
                      <div className="info-value">{block.timestamp ?? '—'}</div>
                    </div>
                    <div className="info-item">
                      <div className="info-label">Status</div>
                      <div className="info-value">{block.status ?? 'Confirmed'}</div>
                    </div>
                  </div>
                  <button
                    className="view-details-button"
                    onClick={() => setSelectedBlock(block)}
                  >
                    View Full Details
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal */}
        {selectedBlock && (
          <div className="modal-overlay" onClick={() => setSelectedBlock(null)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Block Details — #{selectedBlock.id}</h2>
                <button onClick={() => setSelectedBlock(null)}>×</button>
              </div>
              <div className="modal-body">
                <div className="detail-row"><span>Hash:</span>      <code>{selectedBlock.hash}</code></div>
                <div className="detail-row"><span>Prev Hash:</span> <code>{selectedBlock.prev_hash}</code></div>
                <div className="detail-row"><span>Timestamp:</span> <span>{selectedBlock.timestamp}</span></div>
                <div className="detail-row"><span>Status:</span>    <span>{selectedBlock.status}</span></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default BlockchainPage;