/**
 * src/components/QrScanModal.jsx
 *
 * A modal that opens the device camera to scan a QR code.
 * On success, calls onScan(decodedText).
 * Falls back to a manual tag entry form if camera access is denied.
 */

import { useEffect, useRef, useState } from 'react';
import { Html5QrcodeScanner, Html5QrcodeScanType } from 'html5-qrcode';

export default function QrScanModal({ onScan, onClose }) {
  const scannerRef = useRef(null);
  const [cameraError, setCameraError] = useState(false);
  const [manualTag, setManualTag] = useState('');

  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      'qr-reader',
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
        rememberLastUsedCamera: true,
      },
      /* verbose= */ false
    );

    scanner.render(
      (decodedText) => {
        scanner.clear().catch(console.error);
        onScan(decodedText);
      },
      (errorMsg) => {
        // Camera permission denied — show fallback
        if (
          errorMsg.includes('NotAllowedError') ||
          errorMsg.includes('permission')
        ) {
          setCameraError(true);
          scanner.clear().catch(console.error);
        }
      }
    );

    scannerRef.current = scanner;

    return () => {
      scanner.clear().catch(console.error);
    };
  }, []);

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (manualTag.trim()) {
      onScan(manualTag.trim().toUpperCase());
    }
  };

  return (
    <div
      id="qr-scan-modal"
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        background: '#fff', borderRadius: '12px', padding: '24px',
        width: '360px', maxWidth: '90vw', boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0 }}>📷 Scan Asset QR Code</h3>
          <button
            id="qr-modal-close"
            onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        {!cameraError ? (
          <>
            <div id="qr-reader" />
            <p style={{ fontSize: '12px', color: '#888', marginTop: '8px', textAlign: 'center' }}>
              Point camera at an asset QR code
            </p>
            <div style={{ marginTop: '16px', borderTop: '1px solid #eee', paddingTop: '16px' }}>
              <p style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>Or enter tag manually:</p>
              <form onSubmit={handleManualSubmit} style={{ display: 'flex', gap: '8px' }}>
                <input
                  id="qr-manual-tag-input"
                  type="text"
                  placeholder="e.g. AF-0001"
                  value={manualTag}
                  onChange={(e) => setManualTag(e.target.value)}
                  className="filter-input"
                  style={{ flex: 1 }}
                />
                <button type="submit" className="btn btn-primary" style={{ whiteSpace: 'nowrap' }}>
                  Go
                </button>
              </form>
            </div>
          </>
        ) : (
          <div>
            <p style={{ color: '#e74c3c', marginBottom: '12px' }}>
              ⚠️ Camera access denied. Enter the asset tag manually:
            </p>
            <form onSubmit={handleManualSubmit} style={{ display: 'flex', gap: '8px' }}>
              <input
                id="qr-manual-tag-fallback"
                type="text"
                placeholder="e.g. AF-0001"
                value={manualTag}
                onChange={(e) => setManualTag(e.target.value)}
                className="filter-input"
                style={{ flex: 1 }}
                autoFocus
              />
              <button type="submit" className="btn btn-primary" style={{ whiteSpace: 'nowrap' }}>
                Search
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
