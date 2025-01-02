const express = require('express');
const multer = require('multer');
const cors = require('cors');
const session = require('express-session');
const { v4: uuidv4 } = require('uuid');
const { uploadToS3, deleteFromS3, listFilesFromS3, deleteUserFolder } = require('./utils/s3Service');
require('dotenv').config();
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 5000;

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: true,
  cookie: { 
    secure: process.env.NODE_ENV === 'production',
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Middleware to ensure user has ID
app.use((req, res, next) => {
  if (!req.session.userId) {
    req.session.userId = uuidv4();
    require('fs').appendFileSync('.env', `\nCURRENT_USER_ID=${req.session.userId}`);
    process.env.CURRENT_USER_ID = req.session.userId;
  }
  next();
});

// Middleware
app.use(cors({
    origin: 'http://localhost:5001',
    credentials: true
  }));
app.use(express.json());

// Multer configuration for PDF uploads
const storage = multer.memoryStorage();
const upload = multer({
    storage: storage,
    limits: {
        files: 10, // Maximum 10 files
        fileSize: 10 * 1024 * 1024 // 10MB limit per file
    },
    fileFilter: (req, file, cb) => {
        if (file.mimetype === 'application/pdf') {
            cb(null, true);
        } else {
            cb(new Error('Only PDF files are allowed'));
        }
    }
});

// Routes
app.post('/upload', upload.array('pdfs', 10), async (req, res) => {
    try {
        const uploadedFiles = req.files;
        const savedFiles = [];
        const userId = req.session.userId;

        for (const file of uploadedFiles) {
            const result = await uploadToS3(file, file.originalname, userId);
            savedFiles.push({
                id: result.key,
                filename: file.originalname
            });
        }

        res.status(200).json({
            message: 'Files uploaded successfully',
            files: savedFiles
        });
    } catch (error) {
        res.status(500).json({
            message: 'Error uploading files',
            error: error.message
        });
    }
});

app.get('/files', async (req, res) => {
    try {
        const userId = req.session.userId;
        const files = await listFilesFromS3(userId);
        
        if (!files || files.length === 0) {
            return res.status(200).json([]);
        }

        const formattedFiles = files.map(file => ({
            _id: file._id,
            filename: file.filename,
            uploadDate: file.uploadDate
        }));
        
        res.status(200).json(formattedFiles);
    } catch (error) {
        res.status(500).json({
            message: 'Error fetching files',
            error: error.message
        });
    }
});

app.delete('/files/:id', async (req, res) => {
    try {
        const userId = req.session.userId;
        await deleteFromS3(req.params.id, userId);
        res.status(200).json({ message: 'File deleted successfully' });
    } catch (error) {
        res.status(500).json({
            message: 'Error deleting file',
            error: error.message
        });
    }
});

app.delete('/files', async (req, res) => {
    try {
        const userId = req.session.userId;
        await deleteUserFolder(userId);
        res.status(200).json({ message: 'All files deleted successfully' });
    } catch (error) {
        res.status(500).json({
            message: 'Error deleting all files',
            error: error.message
        });
    }
});

// Add new endpoint for text extraction
app.post('/extract-text', async (req, res) => {
    try {
        const userId = req.session.userId;
        
        // Spawn Python process with userId as argument
        const pythonProcess = spawn('python', ['extract_text.py', userId]);
        
        let result = '';
        let error = '';

        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            error += data.toString();
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                return res.status(500).json({ 
                    error: 'Error processing PDFs',
                    details: error 
                });
            }
            try {
                const parsedResult = JSON.parse(result);
                res.status(200).json(parsedResult);
            } catch (e) {
                res.status(500).json({ 
                    error: 'Error parsing Python output',
                    details: result 
                });
            }
        });
    } catch (error) {
        res.status(500).json({
            message: 'Error extracting text',
            error: error.message
        });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
}); 
