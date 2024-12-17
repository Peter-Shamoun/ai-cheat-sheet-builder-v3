const express = require('express');
const mongoose = require('mongoose');
const multer = require('multer');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

const db = mongoose.connection;
db.on('error', console.error.bind(console, 'MongoDB connection error:'));
db.once('open', () => console.log('Connected to MongoDB'));

// PDF Schema
const pdfSchema = new mongoose.Schema({
    filename: String,
    data: Buffer,
    uploadDate: { type: Date, default: Date.now }
});

const PDF = mongoose.model('PDF', pdfSchema);

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
            const newPDF = new PDF({
                filename: file.originalname,
                data: file.buffer
            });
            await newPDF.save();
            savedFiles.push({
                id: newPDF._id,
                filename: newPDF.filename
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
        const files = await PDF.find({}, 'filename uploadDate');
        res.status(200).json(files);
    } catch (error) {
        res.status(500).json({
            message: 'Error fetching files',
            error: error.message
        });
    }
});

app.delete('/files/:id', async (req, res) => {
    try {
        await PDF.findByIdAndDelete(req.params.id);
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
        await PDF.deleteMany({});
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