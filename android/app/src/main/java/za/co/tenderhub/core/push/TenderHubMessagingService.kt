package za.co.tenderhub.core.push
import android.Manifest
import android.app.*
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import za.co.tenderhub.MainActivity
import kotlinx.coroutines.flow.MutableSharedFlow
object PushEvents{val received=MutableSharedFlow<Unit>(extraBufferCapacity=1);val tokenChanged=MutableSharedFlow<Unit>(extraBufferCapacity=1)}
class TenderHubMessagingService:FirebaseMessagingService(){override fun onNewToken(token:String){PushRegistrationManager(this).onTokenChanged(token);PushEvents.tokenChanged.tryEmit(Unit)}
 override fun onMessageReceived(message:RemoteMessage){PushEvents.received.tryEmit(Unit);val title=message.notification?.title?:"TenderHub SA";val body=message.notification?.body?:return;val tenderId=message.data["tender_id"];val channel="tender_alerts";val manager=getSystemService(NotificationManager::class.java);manager.createNotificationChannel(NotificationChannel(channel,"Tender alerts",NotificationManager.IMPORTANCE_DEFAULT));val intent=Intent(this,MainActivity::class.java).apply{data=Uri.parse(if(tenderId.isNullOrBlank())"tenderhub://notifications" else "tenderhub://tender/$tenderId");flags=Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP};val pending=PendingIntent.getActivity(this,(tenderId?:message.messageId?:"notification").hashCode(),intent,PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE);val notification=NotificationCompat.Builder(this,channel).setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle(title).setContentText(body).setAutoCancel(true).setContentIntent(pending).build();if(ActivityCompat.checkSelfPermission(this,Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)manager.notify((message.messageId?:System.currentTimeMillis().toString()).hashCode(),notification)} }
