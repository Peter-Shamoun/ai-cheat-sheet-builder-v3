const { S3Client, PutObjectCommand, DeleteObjectCommand, ListObjectsV2Command } = require('@aws-sdk/client-s3');
require('dotenv').config();

const s3Client = new S3Client({
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.aws_access_key,
    secretAccessKey: process.env.aws_secret_key,
  },
});

const uploadToS3 = async (file, filename) => {
  const params = {
    Bucket: process.env.bucket_name,
    Key: filename,
    Body: file.buffer,
    ContentType: file.mimetype,
  };

  try {
    await s3Client.send(new PutObjectCommand(params));
    return {
      success: true,
      key: filename
    };
  } catch (error) {
    console.error('Error uploading to S3:', error);
    throw error;
  }
};

const deleteFromS3 = async (filename) => {
  const params = {
    Bucket: process.env.bucket_name,
    Key: filename,
  };

  try {
    await s3Client.send(new DeleteObjectCommand(params));
    return {
      success: true
    };
  } catch (error) {
    console.error('Error deleting from S3:', error);
    throw error;
  }
};

const listFilesFromS3 = async () => {
  const params = {
    Bucket: process.env.bucket_name,
  };

  try {
    const data = await s3Client.send(new ListObjectsV2Command(params));
    return data.Contents || [];
  } catch (error) {
    console.error('Error listing files from S3:', error);
    throw error;
  }
};

module.exports = {
  uploadToS3,
  deleteFromS3,
  listFilesFromS3
}; 