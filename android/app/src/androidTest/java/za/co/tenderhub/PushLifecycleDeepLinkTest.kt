package za.co.tenderhub

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import za.co.tenderhub.core.push.PushMessageRouter

class PushLifecycleDeepLinkTest {
    private val payload = mapOf(
        "notification_id" to "notification-1",
        "title" to "Tender updated",
        "body" to "Closing date changed",
        "type" to "TENDER_UPDATED",
        "tender_id" to "tender-123",
    )

    @Test
    fun foregroundDataPushRoutesToTender() {
        assertEquals("tenderhub://tender/tender-123", PushMessageRouter.fromData(payload)?.deepLink.toString())
    }

    @Test
    fun backgroundDataPushRoutesToTender() {
        assertEquals("tender-123", PushMessageRouter.fromData(payload)?.tenderId)
    }

    @Test
    fun terminatedAppIntentRetainsTenderId() {
        assertEquals("tenderhub://tender/tender-123", PushMessageRouter.fromData(payload)?.deepLink.toString())
    }

    @Test
    fun missingTenderRoutesToNotificationCenter() {
        assertEquals(
            "tenderhub://notifications",
            PushMessageRouter.fromData(payload - "tender_id")?.deepLink.toString(),
        )
    }

    @Test
    fun invalidPayloadIsIgnored() {
        assertNull(PushMessageRouter.fromData(emptyMap()))
    }

    @Test
    fun invalidOrMissingTenderPathDoesNotCrashRouter() {
        assertNull(resolveTenderHubDeepLink(android.net.Uri.parse("tenderhub://tender")))
        assertEquals(
            "missing-tender",
            resolveTenderHubDeepLink(android.net.Uri.parse("tenderhub://tender/missing-tender")),
        )
    }
}
