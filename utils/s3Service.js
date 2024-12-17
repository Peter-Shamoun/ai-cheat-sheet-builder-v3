const { S3Client, PutObjectCommand, DeleteObjectCommand, ListObjectsV2Command, DeleteObjectsCommand } = require('@aws-sdk/client-s3');
require('dotenv').config();

const s3Client = new S3Client({
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.aws_access_key,
    secretAccessKey: process.env.aws_secret_key,
  },
});

const uploadToS3 = async (file, filename, userId) => {
  // Create a user-specific key prefix
  const userPrefix = `user_${userId}/`;
  const key = userPrefix + filename;

  const params = {
    Bucket: process.env.bucket_name,
    Key: key,
    Body: file.buffer,
    ContentType: file.mimetype,
    Metadata: {
      userId: userId
    }
  };

  try {
    await s3Client.send(new PutObjectCommand(params));
    return {
      success: true,
      key: key
    };
  } catch (error) {
    console.error('Error uploading to S3:', error);
    throw error;
  }
};

const deleteFromS3 = async (filename, userId) => {
  // Ensure the filename includes the user prefix
  const key = filename.startsWith(`user_${userId}/`) ? filename : `user_${userId}/${filename}`;
  
  const params = {
    Bucket: process.env.bucket_name,
    Key: key,
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

const listFilesFromS3 = async (userId) => {
  const params = {
    Bucket: process.env.bucket_name,
    Prefix: `user_${userId}/`
  };

  try {
    const data = await s3Client.send(new ListObjectsV2Command(params));
    return (data.Contents || []).map(file => ({
      _id: file.Key,
      filename: file.Key.replace(`user_${userId}/`, ''),
      uploadDate: file.LastModified
    }));
  } catch (error) {
    console.error('Error listing files from S3:', error);
    throw error;
  }
};

const deleteUserFolder = async (userId) => {
  const params = {
    Bucket: process.env.bucket_name,
    Prefix: `user_${userId}/`
  };

  try {
    // First, list all objects with the user's prefix
    const listResponse = await s3Client.send(new ListObjectsV2Command(params));
    
    if (!listResponse.Contents || listResponse.Contents.length === 0) {
      return { success: true };
    }

    // Prepare the objects for deletion
    const deleteParams = {
      Bucket: process.env.bucket_name,
      Delete: {
        Objects: listResponse.Contents.map(obj => ({ Key: obj.Key })),
        Quiet: true
      }
    };

    // Delete all objects in the folder
    await s3Client.send(new DeleteObjectsCommand(deleteParams));
    
    return { success: true };
  } catch (error) {
    console.error('Error deleting user folder from S3:', error);
    throw error;
  }
};

module.exports = {
  uploadToS3,
  deleteFromS3,
  listFilesFromS3,
  deleteUserFolder
}; 