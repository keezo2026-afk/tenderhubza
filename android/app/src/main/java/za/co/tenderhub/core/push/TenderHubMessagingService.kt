package za.co.tenderhub.core.push

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.flow.MutableSharedFlow
import za.co.tenderhub.MainActivity

object PushEvents {
    val received = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val tokenChanged = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
}

class TenderHubMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        PushRegistrationManager(this).onTokenChanged(token)
        PushEvents.tokenChanged.tryEmit(Unit)
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val payload = PushMessageRouter.fromData(message.data) ?: return
        PushEvents.received.tryEmit(Unit)
        val channelId = "tender_alerts"
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(channelId, "Tender alerts", NotificationManager.IMPORTANCE_DEFAULT)
        )
        val intent = Intent(this, MainActivity::class.java).apply {
            data = payload.deepLink
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            payload.notificationId.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(payload.title)
            .setContentText(payload.body)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()
        if (
            ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) ==
                PackageManager.PERMISSION_GRANTED
        ) {
            manager.notify(payload.notificationId.hashCode(), notification)
        }
    }
}
