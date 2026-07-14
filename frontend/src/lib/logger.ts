type LogLevel = 'INFO' | 'WARNING' | 'ERROR'

type LogContext = Record<string, string | number | boolean | undefined>

interface LogEntry extends LogContext {
  timestamp: string
  level: LogLevel
  message: string
  service: string
}

class Logger {
  private readonly service = 'kartoteka-web'
  private readonly isServer = typeof window === 'undefined'

  private write(level: LogLevel, message: string, context?: LogContext): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      service: this.service,
      ...context,
    }

    if (this.isServer) {
      // eslint-disable-next-line no-console -- единственная точка вывода на сервере
      console.log(JSON.stringify(entry))
      return
    }

    const method = level === 'ERROR' ? 'error' : level === 'WARNING' ? 'warn' : 'log'
    // eslint-disable-next-line no-console -- единственная точка вывода в браузере
    console[method](`[${level}]`, message, entry)
  }

  info(message: string, context?: LogContext): void {
    this.write('INFO', message, context)
  }

  warn(message: string, context?: LogContext): void {
    this.write('WARNING', message, context)
  }

  error(message: string, error?: unknown, context?: LogContext): void {
    const errorContext: LogContext = { ...context }

    if (error instanceof Error) {
      errorContext.error = error.message
      errorContext.error_type = error.name
    } else if (error !== undefined) {
      errorContext.error = String(error)
    }

    this.write('ERROR', message, errorContext)
  }
}

export const logger = new Logger()
