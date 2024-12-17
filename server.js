const express = require('express');
const multer = require('multer');
const cors = require('cors');
const { uploadToS3, deleteFromS3, listFilesFromS3 } = require('./utils/s3Service');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
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

        for (const file of uploadedFiles) {
            const result = await uploadToS3(file, file.originalname);
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
        const files = await listFilesFromS3();
        const formattedFiles = files.map(file => ({
            _id: file.Key,
            filename: file.Key,
            uploadDate: file.LastModified
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
        await deleteFromS3(req.params.id);
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
        const files = await listFilesFromS3();
        await Promise.all(files.map(file => deleteFromS3(file.Key)));
        res.status(200).json({ message: 'All files deleted successfully' });
    } catch (error) {
        res.status(500).json({
            message: 'Error deleting all files',
            error: error.message
        });
    }
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
}); 