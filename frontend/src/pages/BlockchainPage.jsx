import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api'; // ✅ WEEK 9
import './BlockchainPage.css';

const BlockchainPage = () => {
  const [blocks, setBlocks] = useState([
    {
      id: 1, height: 12543,
      hash: '0x7a8f3e2d9b4c1a5f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5',
      previousHash: '0x9b4c1a5f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1',
      timestamp: new Date().toLocaleString('en-GB', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).replace(/\//g, '-'),
      size: '1.24', gasPrice: '24', status: 'confirmed'
    },
    {
      id: 2, height: 12542,
      hash: '0x9b4c1a5f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1',
      previousHash: '0x2d6e4b8c7a9f3e1d5c0b4a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8',
      timestamp: new Date(Date.now() - 5 * 60000).toLocaleString('en-GB').replace(/\//g, '-'),
      size: '0.98', gasPrice: '31', status: 'confirmed'
    }
  ]);

  const [stats, setStats] = useState({ totalBlocks: 12543, avgGasPrice: 28 });
  const [selectedBlock, setSelectedBlock] = useState(null);

  const generateHash = () => {
    const chars = '0123456789abcdef';
    let hash = '0x';
    for (let i = 0; i < 64; i++) hash += chars[Math.floor(Math.random() * chars.length)];
    return hash;
  };

  const createNewBlock = (prevBlock) => {
    const newGas = Math.floor(Math.random() * 20) + 15;
    return {
      id: prevBlock.id + 1, height: prevBlock.height + 1,
      hash: generateHash(), previousHash: prevBlock.hash,
      timestamp: new Date().toLocaleString('en-GB').replace(/\//g, '-'),
      size: (Math.random() * (1.5 - 0.5) + 0.5).toFixed(2),
      gasPrice: newGas, status: 'confirmed'
    };
  };

  // ✅ WEEK 9: Backend se blockchain data fetch karna (token ke saath)
  const fetchBlockchainData = async () => {
    try {
      const res = await authenticatedFetch('http://localhost:8000/api/blockchain');
      if (!res) return; // 401 handled — user redirected to /login
      const data = await res.json();
      if (data && data.blocks && data.blocks.length > 0) {
        setBlocks(data.blocks);
      }
    } catch (err) {
      console.log('Backend not available, using demo data.');
    }
  };

  useEffect(() => {
    fetchBlockchainData(); // ✅ Page load pe backend se data lo
  }, []);

  useEffect(() => {
    const blockInterval = setInterval(() => {
      setBlocks(prev => {
        const next = createNewBlock(prev[0]);
        setStats(s => ({ totalBlocks: s.totalBlocks + 1, avgGasPrice: Math.floor((s.avgGasPrice + next.gasPrice) / 2) }));
        return [next, ...prev].slice(0, 10);
      });
    }, 10000);
    return () => clearInterval(blockInterval);
  }, []);

  const handleSync = () => {
    fetchBlockchainData(); // ✅ WEEK 9: Backend se sync karo
    setBlocks(prev => [createNewBlock(prev[0]), ...prev].slice(0, 10));
    setStats(s => ({ ...s, totalBlocks: s.totalBlocks + 1 }));
  };

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

        <div className="blockchain-stats-grid">
          <div className="stat-card-blockchain">
            <div className="stat-content-blockchain">
              <div className="stat-value-blockchain">{stats.totalBlocks.toLocaleString()}</div>
              <div className="stat-label-blockchain">Total Blocks</div>
            </div>
          </div>
          <div className="stat-card-blockchain">
            <div className="stat-content-blockchain">
              <div className="stat-value-blockchain">{stats.avgGasPrice} Gwei</div>
              <div className="stat-label-blockchain">Avg. Gas Price</div>
            </div>
          </div>
        </div>

        <div className="blocks-section">
          <div className="blocks-list">
            {blocks.map((block) => (
              <div key={block.id} className="block-card">
                <div className="block-header">
                  <div className="block-height">Block #{block.height}</div>
                  <span className="block-status confirmed">Confirmed</span>
                </div>
                <div className="block-info-grid">
                  <div className="info-item">
                    <div className="info-label">Hash</div>
                    <code className="info-value">{block.hash.substring(0, 16)}...</code>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Block Size</div>
                    <div className="info-value">{block.size} MB</div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Timestamp</div>
                    <div className="info-value">{block.timestamp}</div>
                  </div>
                  <div className="info-item">
                    <div className="info-label">Gas Price</div>
                    <div className="info-value">{block.gasPrice} Gwei</div>
                  </div>
                </div>
                <button className="view-details-button" onClick={() => setSelectedBlock(block)}>View Full Details</button>
              </div>
            ))}
          </div>
        </div>

        {selectedBlock && (
          <div className="modal-overlay" onClick={() => setSelectedBlock(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Block Details - #{selectedBlock.height}</h2>
                <button onClick={() => setSelectedBlock(null)}>×</button>
              </div>
              <div className="modal-body">
                <div className="detail-row"><span>Hash:</span> <code>{selectedBlock.hash}</code></div>
                <div className="detail-row"><span>Prev Hash:</span> <code>{selectedBlock.previousHash}</code></div>
                <div className="detail-row"><span>Size:</span> <span>{selectedBlock.size} MB</span></div>
                <div className="detail-row"><span>Gas Price:</span> <span>{selectedBlock.gasPrice} Gwei</span></div>
                <div className="detail-row"><span>Timestamp:</span> <span>{selectedBlock.timestamp}</span></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default BlockchainPage;