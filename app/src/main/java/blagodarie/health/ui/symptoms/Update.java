package blagodarie.health.ui.symptoms;

import androidx.annotation.NonNull;

import blagodarie.health.BuildConfig;

enum Update {

    MANDATORY, OPTIONAL, NO;

    @NonNull
    static Update determine (@NonNull final VersionName newVersionName) {
        Update update;
        final VersionName currentVersionName = new VersionName(BuildConfig.VERSION_NAME);
        if (currentVersionName.getMajorSegment() < newVersionName.getMajorSegment() ||
                (currentVersionName.getMajorSegment() == newVersionName.getMajorSegment() &&
                        currentVersionName.getMiddleSegment() < newVersionName.getMiddleSegment())) {
            update = MANDATORY;
        } else if (currentVersionName.getMajorSegment() == newVersionName.getMajorSegment() &&
                currentVersionName.getMiddleSegment() == newVersionName.getMiddleSegment() &&
                currentVersionName.getMinorSegment() < newVersionName.getMinorSegment()) {
            update = OPTIONAL;
        } else {
            update = NO;
        }
        return update;
    }
}
