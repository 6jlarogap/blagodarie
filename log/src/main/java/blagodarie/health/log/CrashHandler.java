package blagodarie.health.log;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

import androidx.annotation.NonNull;

public final class CrashHandler
        implements Thread.UncaughtExceptionHandler {

    private static final String TAG = CrashHandler.class.getSimpleName();

    @NonNull
    private final Context mContext;

    public CrashHandler (@NonNull final Context context) {
        mContext = context;
    }

    @Override
    public void uncaughtException (
            @NonNull final Thread t,
            @NonNull final Throwable e
    ) {
        Log.d(TAG, "handleUncaughtException");
        Log.e(TAG, Log.getStackTraceString(e));

        final Intent intent = new Intent();
        intent.setAction(LogActivity.ACTION_SEND_LOG);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        mContext.startActivity(intent);

        System.exit(1);
    }

}
