import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { InputOTP, InputOTPGroup, InputOTPSlot } from '@/components/ui/input-otp';
import { Globe, Mail } from 'lucide-react';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('email');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { login } = React.useContext(AuthContext);

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/auth/send-otp', { email });
      toast.success(t('login.otpSent'));
      setStep('otp');
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      // Map backend errors to localized messages
      if (errorDetail === 'No OTP requested for this email') {
        toast.error(t('login.otpNotRequested'));
      } else {
        toast.error(t('common.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post('/auth/verify-otp', { email, otp });
      login(response.data.token, response.data.user);
      toast.success(t('common.success'));
      navigate('/albums');
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      // Map backend errors to localized messages
      if (errorDetail === 'Invalid OTP') {
        toast.error(t('login.otpInvalid'));
      } else if (errorDetail === 'OTP expired') {
        toast.error(t('login.otpExpired'));
      } else if (errorDetail === 'No OTP requested for this email') {
        toast.error(t('login.otpNotRequested'));
      } else {
        toast.error(t('common.error'));
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'es' ? 'en' : 'es';
    i18n.changeLanguage(newLang);
  };

  return (
    <div className="min-h-screen login-bg flex items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <Button
          data-testid="language-toggle-btn"
          variant="outline"
          size="icon"
          onClick={toggleLanguage}
          className="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/20 text-white"
        >
          <Globe className="h-5 w-5" />
        </Button>
      </div>

      <div className="w-full max-w-md bg-white/95 backdrop-blur-lg p-8 rounded-3xl shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-black tracking-tight text-primary mb-2">
            {t('login.title')}
          </h1>
          <p className="text-base text-muted-foreground">{t('login.subtitle')}</p>
        </div>

        {step === 'email' ? (
          <form onSubmit={handleSendOTP} className="space-y-6" data-testid="email-form">
            <div>
              <Input
                data-testid="email-input"
                type="email"
                placeholder={t('login.emailPlaceholder')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-12 text-base"
              />
            </div>
            <Button
              data-testid="send-otp-btn"
              type="submit"
              className="w-full h-12 btn-primary text-base"
              disabled={loading}
            >
              {loading ? t('common.loading') : t('login.sendOTP')}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP} className="space-y-6" data-testid="otp-form">
            {/* Email notification - OTP is sent by email, never shown in UI */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    {t('login.checkEmail')}
                  </p>
                  <p className="text-xs text-blue-700">{email}</p>
                </div>
              </div>
            </div>
            
            <div className="flex flex-col items-center space-y-4">
              <InputOTP
                data-testid="otp-input"
                maxLength={6}
                value={otp}
                onChange={(value) => setOtp(value)}
              >
                <InputOTPGroup>
                  <InputOTPSlot index={0} />
                  <InputOTPSlot index={1} />
                  <InputOTPSlot index={2} />
                  <InputOTPSlot index={3} />
                  <InputOTPSlot index={4} />
                  <InputOTPSlot index={5} />
                </InputOTPGroup>
              </InputOTP>
            </div>
            <Button
              data-testid="verify-otp-btn"
              type="submit"
              className="w-full h-12 btn-primary text-base"
              disabled={loading || otp.length !== 6}
            >
              {loading ? t('common.loading') : t('login.verify')}
            </Button>
            <Button
              data-testid="resend-otp-btn"
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => setStep('email')}
            >
              {t('login.resend')}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Login;
