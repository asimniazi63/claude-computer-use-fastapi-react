import React, { useState } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Divider,
  Alert,
} from '@mui/material';
import {
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  CloudUpload as UploadIcon,
  CloudDownload as DownloadIcon,
} from '@mui/icons-material';

interface FileManagerProps {
  sessionId: string;
}

const FileManager: React.FC<FileManagerProps> = ({ sessionId }) => {
  const [files] = useState([
    { name: 'desktop', type: 'folder' },
    { name: 'downloads', type: 'folder' },
    { name: 'documents', type: 'folder' },
    { name: 'example.txt', type: 'file' },
    { name: 'screenshot.png', type: 'file' },
  ]);

  const handleFileClick = (fileName: string) => {
    console.log(`File clicked: ${fileName}`);
    // TODO: Implement file operations
  };

  const handleUpload = () => {
    console.log('Upload file');
    // TODO: Implement file upload
  };

  const handleDownload = (fileName: string) => {
    console.log(`Download file: ${fileName}`);
    // TODO: Implement file download
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">File Management</Typography>
          <IconButton size="small" onClick={handleUpload}>
            <UploadIcon />
          </IconButton>
        </Box>
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Alert severity="info" sx={{ m: 1 }}>
          File management functionality coming soon!
        </Alert>

        <List dense>
          {files.map((file, index) => (
            <React.Fragment key={file.name}>
              <ListItem
                button
                onClick={() => handleFileClick(file.name)}
                secondaryAction={
                  file.type === 'file' && (
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(file.name);
                      }}
                    >
                      <DownloadIcon />
                    </IconButton>
                  )
                }
              >
                <ListItemIcon>
                  {file.type === 'folder' ? <FolderIcon /> : <FileIcon />}
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
              {index < files.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </Box>
    </Box>
  );
};

export default FileManager;
