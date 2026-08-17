package za.co.tenderhub.core.push

import android.net.Uri

data class TenderPushPayload(
    val notificationId: String,
    val title: String,
    val body: String,
    val tenderId: String?,
    val type: String,
) {
    val deepLink: Uri
        get() = if (tenderId.isNullOrBlank()) {
            Uri.parse("tenderhub://notifications")
        } else {
            Uri.parse("tenderhub://tender/${Uri.encode(tenderId)}")
        }
}

object PushMessageRouter {
    fun fromData(data: Map<String, String>): TenderPushPayload? {
        val notificationId = data["notification_id"]?.takeIf { it.isNotBlank() } ?: return null
        val title = data["title"]?.takeIf { it.isNotBlank() } ?: "TenderHub SA"
        val body = data["body"]?.takeIf { it.isNotBlank() } ?: return null
        return TenderPushPayload(
            notificationId = notificationId,
            title = title,
            body = body,
            tenderId = data["tender_id"]?.takeIf { it.isNotBlank() },
            type = data["type"].orEmpty(),
        )
    }
}
