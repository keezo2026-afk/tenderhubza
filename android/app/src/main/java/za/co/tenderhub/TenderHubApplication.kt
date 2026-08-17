package za.co.tenderhub
import android.app.Application
import za.co.tenderhub.core.auth.SecureTokenStore
import za.co.tenderhub.core.network.ApiFactory
import za.co.tenderhub.data.repository.NetworkAuthRepository
class TenderHubApplication:Application(){val authRepository by lazy{val tokens=SecureTokenStore(this);NetworkAuthRepository(ApiFactory.create(tokens),tokens)}}
