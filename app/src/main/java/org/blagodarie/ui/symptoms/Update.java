package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;

import org.blagodarie.BuildConfig;

enum Update {

    MANDATORY, OPTIONAL, NO;

    @NonNull
    static Update determine (@NonNull final VersionName newVersionName) {
        Update update;
        final VersionName currentVersionName = new VersionName(BuildConfig.VERSION_NAME.replace("-dbg", ""));
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
