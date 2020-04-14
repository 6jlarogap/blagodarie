package org.blagodarie.ui.update;

import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.database.Cursor;
import android.net.Uri;

import androidx.annotation.NonNull;

import java.io.File;
import java.util.Timer;
import java.util.TimerTask;

import static android.content.Context.DOWNLOAD_SERVICE;

class UpdateManager {

    interface ProgressListener {
        void onNext (final long total, final long downloaded);
        void onSuccess();
        void onFail();
    }

    enum DownloadStatus {
        WAIT, RUN, SUCCESS, FAIL
    }

    private static volatile UpdateManager INSTANCE;

    private static final String MIME_TYPE = "application/vnd.android.package-archive";

    private long mDownloadId;

    private ProgressListener mProgressListener;

    private DownloadStatus mDownloadStatus = DownloadStatus.WAIT;

    private UpdateManager () {
    }

    static UpdateManager getInstance (
    ) {
        synchronized (UpdateManager.class) {
            if (INSTANCE == null) {
                INSTANCE = new UpdateManager();
            }
        }
        return INSTANCE;
    }

    void setProgressListener(@NonNull final ProgressListener progressListener){
        mProgressListener = progressListener;
    }

    DownloadStatus getDownloadStatus () {
        return mDownloadStatus;
    }

    void startDownload (
            @NonNull final Context context,
            @NonNull final File apkFile,
            @NonNull final Uri latestVersionUri
    ) {
        if (mDownloadStatus == DownloadStatus.WAIT) {
            mDownloadStatus = DownloadStatus.RUN;

            DownloadManager.Request request = new DownloadManager.Request(latestVersionUri)
                    .setTitle(apkFile.getName())// Title of the Download Notification
                    .setMimeType(MIME_TYPE)
                    .setDescription("Загрузка")// Description of the Download Notification
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)// Visibility of the download Notification
                    .setDestinationUri(Uri.fromFile(apkFile))// Uri of the destination file
                    .setAllowedOverMetered(true)// Set if download is allowed on Mobile network
                    .setAllowedOverRoaming(true);// Set if download is allowed on roaming network

            DownloadManager downloadManager = (DownloadManager) context.getSystemService(DOWNLOAD_SERVICE);
            mDownloadId = downloadManager.enqueue(request);// enqueue puts the download request in the queue.
            Timer timer = new Timer();
            timer.schedule(new TimerTask() {
                @Override
                public void run () {
                    Cursor cursor = downloadManager.query(new DownloadManager.Query().setFilterById(mDownloadId));
                    if (cursor != null) {
                        if (cursor.moveToFirst()) {
                            if (cursor.moveToFirst()) {
                                int status = cursor.getInt(cursor.getColumnIndex(DownloadManager.COLUMN_STATUS));
                                switch (status) {
                                    case DownloadManager.STATUS_RUNNING: {
                                        final long total = cursor.getLong(cursor.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES));
                                        if (total >= 0) {
                                            final long downloaded = cursor.getLong(cursor.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR));
                                            mProgressListener.onNext(total, downloaded);
                                        }
                                        break;
                                    }
                                    case DownloadManager.STATUS_SUCCESSFUL: {
                                        mDownloadStatus = DownloadStatus.SUCCESS;
                                        mProgressListener.onSuccess();
                                        timer.cancel();
                                        break;
                                    }
                                    case DownloadManager.STATUS_FAILED: {
                                        mDownloadStatus = DownloadStatus.FAIL;
                                        mProgressListener.onFail();
                                        timer.cancel();
                                        break;
                                    }
                                }
                            }
                            cursor.close();
                        }
                    }
                }
            }, 0, 1000);
        }
    }
/*
    private void startInstall (
            @NonNull final Context context,
            @NonNull final File apkFile
    ) {
        String destination = context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS).toString() + "/";
        destination += apkFile.getName();
        Uri uri = Uri.parse(FILE_BASE_PATH + destination);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            Uri contentUri = FileProvider.getUriForFile(
                    context,
                    BuildConfig.APPLICATION_ID + PROVIDER_PATH,
                    new File(destination)
            );
            Intent install = new Intent(Intent.ACTION_VIEW);
            install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            install.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            install.putExtra(Intent.EXTRA_NOT_UNKNOWN_SOURCE, true);
            install.setData(contentUri);
            context.startActivity(install);
        } else {
            Intent install = new Intent(Intent.ACTION_VIEW);
            install.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            install.setDataAndType(
                    uri,
                    APP_INSTALL_PATH
            );
            context.startActivity(install);
        }
    }*/
}
