import React from 'react';
import { Box, Typography, Alert } from '@mui/material';
import { VNCInfo } from '../types';

interface VNCViewerProps {
  vncInfo: VNCInfo | null;
}

const VNCViewer: React.FC<VNCViewerProps> = ({ vncInfo }) => {
  if (!vncInfo) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Loading VNC connection...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">Virtual Machine Screen</Typography>
        <Typography variant="caption" color="text.secondary">
          Display: {vncInfo.display} | Port: {vncInfo.vnc_port}
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1, position: 'relative' }}>
        {/* noVNC iframe */}
        <iframe
          src={vncInfo.vnc_url}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
          }}
          title="VNC Viewer"
        />
      </Box>

      <Alert severity="info" sx={{ m: 1 }}>
        This is a live view of the virtual machine desktop where Claude is operating.
      </Alert>
    </Box>
  );
};

export default VNCViewer;
