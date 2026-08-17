package za.co.tenderhub
import android.app.Application
import za.co.tenderhub.core.auth.SecureTokenStore
import za.co.tenderhub.core.network.ApiFactory
import za.co.tenderhub.data.repository.*
class TenderHubApplication:Application(){private val tokens by lazy{SecureTokenStore(this)};private val api by lazy{ApiFactory.create(tokens)};val authRepository by lazy{NetworkAuthRepository(api,tokens)};val tenderRepository by lazy{NetworkTenderRepository(api)}}
