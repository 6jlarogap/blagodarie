package org.blagodarie.ui.update;

import android.app.DownloadManager;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;

import androidx.annotation.NonNull;

import org.blagodarie.R;

import java.io.File;
import java.util.Timer;
import java.util.TimerTask;

import static android.content.Context.DOWNLOAD_SERVICE;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
final class UpdateManager {

    /**
     * Интерфейс для получения прогресса загрузки.
     */
    interface ProgressListener {
        /**
         * Следующий шаг.
         *
         * @param total      Всего байт.
         * @param downloaded Загружено байт.
         */
        void onNext (final long total, final long downloaded);

        /**
         * Загрузка завершена успешна.
         */
        void onSuccess ();

        /**
         * Загрузка не удалась.
         */
        void onFail ();
    }

    /**
     * Возможные состояния загрузки.
     */
    enum DownloadStatus {
        /**
         * Ожидание загрузки.
         */
        WAIT,
        /**
         * Загрузка в процессе.
         */
        RUN,
        /**
         * Загрузка завершена успешно.
         */
        SUCCESS,
        /**
         * Загрузка не удалась.
         */
        FAIL
    }

    /**
     * Задержка перед перед первым обновлением прогресса загрузки.
     */
    private static final long UPDATE_PROGRESS_DELAY = 0L;

    /**
     * Период обновления прогресса загрузки.
     */
    private static final long UPDATE_PROGRESS_PERIOD = 1000L;

    /**
     * Синглтон. Единственный экземпляр.
     */
    private static volatile UpdateManager INSTANCE;

    /**
     * Тип загружаемого файла.
     */
    private static final String MIME_TYPE = "application/vnd.android.package-archive";

    /**
     * Идентификатор загрузки.
     */
    private long mDownloadId;

    /**
     * Слушатель прогресса загрузки.
     */
    private ProgressListener mProgressListener;

    /**
     * Состояние загрузки.
     */
    private DownloadStatus mDownloadStatus = DownloadStatus.WAIT;

    /**
     * Закрытый коструктор для реализации синглтона.
     */
    private UpdateManager () {
    }

    /**
     * Возвращает единственный экземпляр.
     *
     * @return Синглтон UpdateManager.
     */
    static UpdateManager getInstance (
    ) {
        synchronized (UpdateManager.class) {
            if (INSTANCE == null) {
                INSTANCE = new UpdateManager();
            }
        }
        return INSTANCE;
    }

    /**
     * Устанавливает слушателя прогресса загрузки.
     *
     * @param progressListener Слушатель прогресса загрузки.
     */
    void setProgressListener (@NonNull final ProgressListener progressListener) {
        mProgressListener = progressListener;
    }

    /**
     * Возвращает статус загрузки.
     *
     * @return Статус загрузки.
     */
    DownloadStatus getDownloadStatus () {
        return mDownloadStatus;
    }

    /**
     * Запускает загрузку файла новой версии.
     *
     * @param context          Контест.
     * @param apkFile          Целевой файл.
     * @param latestVersionUri URI файла для загрузки.
     */
    void startDownload (
            @NonNull final Context context,
            @NonNull final File apkFile,
            @NonNull final Uri latestVersionUri
    ) {
        if (mDownloadStatus == DownloadStatus.WAIT) {
            mDownloadStatus = DownloadStatus.RUN;

            DownloadManager.Request request = new DownloadManager.Request(latestVersionUri)
                    .setTitle(apkFile.getName())
                    .setMimeType(MIME_TYPE)
                    .setDescription(context.getString(R.string.download_notification))
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationUri(Uri.fromFile(apkFile))
                    .setAllowedOverMetered(true)
                    .setAllowedOverRoaming(true);

            final DownloadManager downloadManager = (DownloadManager) context.getSystemService(DOWNLOAD_SERVICE);
            mDownloadId = downloadManager.enqueue(request);
            startUpdateProgress(downloadManager);
        }
    }

    /**
     * Запускает обновление прогресса по таймеру.
     *
     * @param downloadManager DownloadManager.
     */
    private void startUpdateProgress (@NonNull final DownloadManager downloadManager) {
        final Timer timer = new Timer();
        timer.schedule(
                getUpdateProgressTask(downloadManager, timer),
                UPDATE_PROGRESS_DELAY,
                UPDATE_PROGRESS_PERIOD);
    }

    /**
     * Создает и возвращает TimerTask для обновления прогресса.
     *
     * @param downloadManager DownloadManager.
     * @param timer           Таймер. Необходим чтобы отключить его после завершения загрузки.
     * @return TimerTask для обновления прогресса.
     */
    private TimerTask getUpdateProgressTask (
            @NonNull final DownloadManager downloadManager,
            @NonNull final Timer timer
    ) {
        return new TimerTask() {
            @Override
            public void run () {
                updateProgress(downloadManager, timer);
            }
        };
    }

    /**
     * Обновляет прогресс загрузки.
     *
     * @param downloadManager DownloadManager.
     * @param timer           Таймер. Необходим чтобы отключить его после завершения загрузки.
     */
    private void updateProgress (
            @NonNull final DownloadManager downloadManager,
            @NonNull final Timer timer
    ) {
        final Cursor cursor = downloadManager.query(new DownloadManager.Query().setFilterById(mDownloadId));
        if (cursor != null) {
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
