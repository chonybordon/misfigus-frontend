import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  es: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Intercambia figuritas con tu álbum',
        defaultUser: 'Usuario'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Intercambia figuritas con tu álbum',
        emailPlaceholder: 'Tu correo electrónico',
        sendOTP: 'Enviar código',
        otpPlaceholder: 'Código de 6 dígitos',
        verify: 'Verificar',
        resend: 'Reenviar código',
        devMode: 'MODO DEV - Código OTP',
        devNote: 'Solo para pruebas. Revisa los logs del backend para más detalles.'
      },
      albums: {
        title: 'Mis Álbumes',
        select: 'Selecciona un álbum',
        active: 'ACTIVO',
        inactive: 'INACTIVO',
        comingSoon: 'PRÓXIMAMENTE',
        noAlbums: 'No hay álbumes disponibles',
        activate: 'Activar álbum',
        activateQuestion: '¿Querés activar este álbum?',
        activateConfirm: 'Activar',
        activateSuccess: 'Álbum activado correctamente',
        activateError: 'Error al activar el álbum'
      },
      albumHome: {
        members: 'Miembros',
        myInventory: 'Mi Inventario',
        duplicates: 'Duplicados',
        matches: 'Intercambios',
        offers: 'Ofertas',
        invite: 'Invitar',
        progress: 'Progreso',
        completed: 'completado',
        manageInventory: 'Gestiona tus figuritas, duplicados y faltantes',
        findTrades: 'Encuentra intercambios con otros coleccionistas',
        joinedSuccess: 'Te has unido al álbum'
      },
      invite: {
        title: 'Invitar al Álbum',
        subtitle: 'Comparte este enlace con quien quieras invitar',
        generate: 'Generar Link de Invitación',
        copy: 'Copiar Link',
        select: 'Seleccionar Link',
        openTab: 'Abrir en Nueva Pestaña',
        copied: '¡Link copiado!',
        expires: 'Expira en 1 hora',
        singleUse: 'Uso único',
        accept: 'Aceptar Invitación',
        accepting: 'Aceptando...',
        expired: 'Este enlace ha expirado',
        used: 'Este enlace ya fue usado',
        invalid: 'Enlace inválido',
        loginFirst: 'Inicia sesión para aceptar la invitación'
      },
      inventory: {
        title: 'Mi Inventario',
        search: 'Buscar figuritas...',
        all: 'Todos',
        missing: 'Faltan',
        have: 'Tengo',
        duplicates: 'Duplicados',
        owned: 'Tengo',
        duplicate: 'Duplicado',
        noDuplicates: 'No tienes duplicados todavía',
        noStickers: 'No se encontraron figuritas'
      },
      matches: {
        title: 'Intercambios Sugeridos',
        youGive: 'Das',
        youGet: 'Recibes',
        noMatches: 'No hay intercambios disponibles',
        updateInventory: 'Actualiza tu inventario para encontrar intercambios',
        netGain: 'Ganas'
      },
      offers: {
        title: 'Ofertas',
        sent: 'Enviadas',
        received: 'Recibidas',
        accept: 'Aceptar',
        reject: 'Rechazar',
        sticker: 'Figurita',
        status: {
          sent: 'Enviada',
          accepted: 'Aceptada',
          rejected: 'Rechazada'
        }
      },
      settings: {
        title: 'Configuración',
        language: 'Idioma',
        spanish: 'Español',
        english: 'English',
        logout: 'Cerrar Sesión',
        profile: 'Mi Perfil'
      },
      profile: {
        title: 'Mi Perfil',
        displayName: 'Nombre y apellido',
        displayNamePlaceholder: 'Ejemplo: Juan Pérez',
        email: 'Correo electrónico',
        save: 'Guardar cambios',
        saved: 'Perfil actualizado correctamente'
      },
      members: {
        title: 'Miembros',
        viewAll: 'Ver todos',
        creator: 'Creador',
        member: 'Miembro',
        testUser: 'Usuario de prueba',
        newTestUser: 'Nuevo usuario (prueba)',
        technicalAccount: 'Cuenta técnica (prueba)'
      },
      common: {
        loading: 'Cargando...',
        error: 'Error',
        success: 'Éxito',
        back: 'Volver',
        close: 'Cerrar',
        cancel: 'Cancelar'
      }
    }
  },
  en: {
    translation: {
      app: {
        name: 'MisFigus',
        tagline: 'Trade stickers with your album'
      },
      login: {
        title: 'MisFigus',
        subtitle: 'Trade stickers with your album',
        emailPlaceholder: 'Your email',
        sendOTP: 'Send Code',
        otpPlaceholder: '6-digit code',
        verify: 'Verify',
        resend: 'Resend Code',
        devMode: 'DEV MODE - OTP Code',
        devNote: 'Testing only. Check backend logs for details.'
      },
      albums: {
        title: 'My Albums',
        select: 'Select an album',
        active: 'ACTIVE',
        comingSoon: 'COMING SOON',
        noAlbums: 'No albums available'
      },
      albumHome: {
        members: 'Members',
        myInventory: 'My Inventory',
        duplicates: 'Duplicates',
        matches: 'Trades',
        offers: 'Offers',
        invite: 'Invite',
        progress: 'Progress',
        completed: 'completed'
      },
      invite: {
        title: 'Invite to Album',
        subtitle: 'Share this link with who you want to invite',
        generate: 'Generate Invite Link',
        copy: 'Copy Link',
        select: 'Select Link',
        openTab: 'Open in New Tab',
        copied: 'Link copied!',
        expires: 'Expires in 1 hour',
        singleUse: 'Single use',
        accept: 'Accept Invitation',
        accepting: 'Accepting...',
        expired: 'This link has expired',
        used: 'This link has already been used',
        invalid: 'Invalid link',
        loginFirst: 'Login to accept the invitation'
      },
      inventory: {
        title: 'My Inventory',
        search: 'Search stickers...',
        all: 'All',
        missing: 'Missing',
        have: 'Have',
        duplicates: 'Duplicates',
        owned: 'Owned',
        duplicate: 'Duplicate'
      },
      matches: {
        title: 'Suggested Trades',
        youGive: 'You Give',
        youGet: 'You Get',
        noMatches: 'No trades available',
        updateInventory: 'Update your inventory to find trades'
      },
      offers: {
        title: 'Offers',
        sent: 'Sent',
        received: 'Received',
        accept: 'Accept',
        reject: 'Reject',
        status: {
          sent: 'Sent',
          accepted: 'Accepted',
          rejected: 'Rejected'
        }
      },
      settings: {
        title: 'Settings',
        language: 'Language',
        spanish: 'Español',
        english: 'English',
        logout: 'Logout'
      },
      common: {
        loading: 'Loading...',
        error: 'Error',
        success: 'Success',
        back: 'Back',
        close: 'Close',
        cancel: 'Cancel'
      }
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    lng: 'es',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
