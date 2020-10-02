package blagodarie.health.sync;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.util.Log;

public final class SyncService
        extends Service {

    private static final String TAG = SyncService.class.getSimpleName();

    public final static String ACTION_SYNC_EXCEPTION = "blagodarie.health.sync.EXCEPTION";
    public final static String EXTRA_EXCEPTION = "blagodarie.health.sync.EXCEPTION";

    private static SyncAdapter sSyncAdapter = null;

    private static final Object sSyncAdapterLock = new Object();

    @Override
    public void onCreate () {
        Log.d(TAG, "onCreate");
        synchronized (sSyncAdapterLock) {
            if (sSyncAdapter == null) {
                sSyncAdapter = new SyncAdapter(getApplicationContext(), true);
            }
        }
    }

    @Override
    public IBinder onBind (Intent intent) {
        Log.d(TAG, "onBind");
        return sSyncAdapter.getSyncAdapterBinder();
    }
}